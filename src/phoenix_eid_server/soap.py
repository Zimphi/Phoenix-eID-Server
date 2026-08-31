"""SOAP 1.1 codec for the mandatory national eID-Interface functions."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .constants import (
    ATTRIBUTE_NAMES,
    DSS_NS,
    EID_NS,
    EID_TYPES,
    RESULT_MAJOR_ERROR,
    RESULT_MAJOR_OK,
    SOAP_NS,
)
from .errors import EIDError, common
from .models import AttributeRequest, AttributeResponse, EIDTypeSelection, UseIDRequest
from .service import EIDService, ServerInfo
from .xmlutil import local_name, one, parse_xml, text

ET.register_namespace("soapenv", SOAP_NS)
ET.register_namespace("eid", EID_NS)
ET.register_namespace("dss", DSS_NS)


class SoapEndpoint:
    def __init__(self, service: EIDService):
        self.service = service

    def dispatch(self, provider_id: str, document: bytes) -> bytes:
        try:
            root = parse_xml(document, self.service.config.max_xml_bytes)
            if root.tag != f"{{{SOAP_NS}}}Envelope":
                raise common("schemaViolation", "SOAP 1.1 Envelope is required")
            body = one(root, "Body")
            operations = list(body) if body is not None else []
            if len(operations) != 1:
                raise common("schemaViolation", "SOAP Body must contain exactly one operation")
            request = operations[0]
            operation = local_name(request.tag)
            if operation == "useIDRequest":
                response = self._use_id(provider_id, request)
            elif operation == "getResultRequest":
                response = self._get_result(provider_id, request)
            elif operation == "getServerInfoRequest":
                response = self._server_info(provider_id)
            else:
                raise common("schemaViolation", "unknown eID-Interface operation")
            return self._envelope(response)
        except EIDError as exc:
            response_name = {
                "useID": "useIDResponse",
                "getResult": "getResultResponse",
            }.get(exc.operation, "ErrorResponse")
            return self._envelope(self._error(response_name, exc))

    def _use_id(self, provider_id: str, element: ET.Element) -> ET.Element:
        operations_node = one(element, "UseOperations")
        operations: dict[str, AttributeRequest] = {}
        for child in operations_node if operations_node is not None else ():
            name = local_name(child.tag)
            if name not in ATTRIBUTE_NAMES or name in operations:
                raise common("schemaViolation", "invalid or duplicated operation")
            try:
                operations[name] = AttributeRequest((child.text or "").strip())
            except ValueError as exc:
                raise common("schemaViolation", f"invalid selection for {name}") from exc
        age_node = one(element, "AgeVerificationRequest", required=False)
        place_node = one(element, "PlaceVerificationRequest", required=False)
        transaction_info = text(element, "TransactionInfo", required=False)
        loa = text(element, "LevelOfAssuranceRequest", required=False)
        eid_types_node = one(element, "EIDTypeRequest", required=False)
        eid_types: dict[str, EIDTypeSelection] = {}
        for child in eid_types_node if eid_types_node is not None else ():
            name = local_name(child.tag)
            if name not in EID_TYPES or name in eid_types:
                raise common("schemaViolation", "invalid or duplicated eID type")
            try:
                eid_types[name] = EIDTypeSelection((child.text or "").strip())
            except ValueError as exc:
                raise common("schemaViolation", f"invalid selection for {name}") from exc
        psk_node = one(element, "PSK", required=False)
        psk_id = text(psk_node, "ID") if psk_node is not None else None
        psk_key_text = text(psk_node, "Key") if psk_node is not None else None
        try:
            parsed = UseIDRequest(
                operations=operations,
                age=int(text(age_node, "Age")) if age_node is not None else None,
                community_id=(text(place_node, "CommunityID") if place_node is not None else None),
                transaction_info=transaction_info,
                loa=loa,
                eid_types=eid_types,
                supplied_psk_id=psk_id,
                supplied_psk=bytes.fromhex(psk_key_text) if psk_key_text else None,
            )
        except (TypeError, ValueError) as exc:
            raise common("schemaViolation", "invalid useID request value") from exc
        session = self.service.use_id(provider_id, parsed)
        response = ET.Element(f"{{{EID_NS}}}useIDResponse")
        session_node = ET.SubElement(response, f"{{{EID_NS}}}Session")
        ET.SubElement(session_node, f"{{{EID_NS}}}ID").text = session.identifier
        ET.SubElement(
            response, f"{{{EID_NS}}}eCardServerAddress"
        ).text = self.service.config.ecard_server_url
        psk = ET.SubElement(response, f"{{{EID_NS}}}PSK")
        ET.SubElement(psk, f"{{{EID_NS}}}ID").text = session.psk_id
        ET.SubElement(psk, f"{{{EID_NS}}}Key").text = bytes(session.psk).hex()
        response.append(self._result())
        return response

    def _get_result(self, provider_id: str, element: ET.Element) -> ET.Element:
        session = one(element, "Session")
        session_id = text(session, "ID")
        try:
            counter = int(text(element, "RequestCounter"))
        except (TypeError, ValueError) as exc:
            raise common("schemaViolation", "RequestCounter must be an integer") from exc
        result = self.service.get_result(provider_id, session_id or "", counter)
        response = ET.Element(f"{{{EID_NS}}}getResultResponse")
        data = ET.SubElement(response, f"{{{EID_NS}}}PersonalData")
        for name in ATTRIBUTE_NAMES:
            if name in result.personal_data:
                ET.SubElement(data, f"{{{EID_NS}}}{name}").text = str(result.personal_data[name])
        if result.fulfils_age is not None:
            node = ET.SubElement(response, f"{{{EID_NS}}}FulfilsAgeVerification")
            ET.SubElement(node, f"{{{EID_NS}}}FulfilsRequest").text = str(
                result.fulfils_age
            ).lower()
        if result.fulfils_place is not None:
            node = ET.SubElement(response, f"{{{EID_NS}}}FulfilsPlaceVerification")
            ET.SubElement(node, f"{{{EID_NS}}}FulfilsRequest").text = str(
                result.fulfils_place
            ).lower()
        allowed = ET.SubElement(response, f"{{{EID_NS}}}OperationsAllowedByUser")
        for name, status in result.operations.items():
            ET.SubElement(allowed, f"{{{EID_NS}}}{name}").text = status.value
        if result.loa:
            ET.SubElement(response, f"{{{EID_NS}}}LevelOfAssuranceResult").text = result.loa
        if result.eid_type:
            eid = ET.SubElement(response, f"{{{EID_NS}}}EIDTypeResponse")
            ET.SubElement(eid, f"{{{EID_NS}}}{result.eid_type}").text = "USED"
        response.append(self._result())
        return response

    def _server_info(self, provider_id: str) -> ET.Element:
        info = self.service.get_server_info(provider_id)
        response = ET.Element(f"{{{EID_NS}}}getServerInfoResponse")
        response.append(self._version(info))
        rights = ET.SubElement(response, f"{{{EID_NS}}}DocumentVerificationRights")
        for name in ATTRIBUTE_NAMES:
            value = (
                AttributeResponse.ALLOWED if name in info.rights else AttributeResponse.PROHIBITED
            )
            ET.SubElement(rights, f"{{{EID_NS}}}{name}").text = value.value
        return response

    @staticmethod
    def _version(info: ServerInfo) -> ET.Element:
        version = ET.Element(f"{{{EID_NS}}}ServerVersion")
        ET.SubElement(version, f"{{{EID_NS}}}VersionString").text = info.version_string
        ET.SubElement(version, f"{{{EID_NS}}}Major").text = str(info.major)
        ET.SubElement(version, f"{{{EID_NS}}}Minor").text = str(info.minor)
        ET.SubElement(version, f"{{{EID_NS}}}Bugfix").text = str(info.bugfix)
        return version

    @staticmethod
    def _result(error: EIDError | None = None) -> ET.Element:
        result = ET.Element(f"{{{DSS_NS}}}Result")
        ET.SubElement(result, f"{{{DSS_NS}}}ResultMajor").text = (
            RESULT_MAJOR_ERROR if error else RESULT_MAJOR_OK
        )
        if error:
            ET.SubElement(result, f"{{{DSS_NS}}}ResultMinor").text = error.result_minor
            ET.SubElement(result, f"{{{DSS_NS}}}ResultMessage").text = error.message
        return result

    def _error(self, response_name: str, error: EIDError) -> ET.Element:
        response = ET.Element(f"{{{EID_NS}}}{response_name}")
        response.append(self._result(error))
        return response

    @staticmethod
    def _envelope(payload: ET.Element) -> bytes:
        envelope = ET.Element(f"{{{SOAP_NS}}}Envelope")
        ET.SubElement(envelope, f"{{{SOAP_NS}}}Header")
        body = ET.SubElement(envelope, f"{{{SOAP_NS}}}Body")
        body.append(payload)
        return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)
