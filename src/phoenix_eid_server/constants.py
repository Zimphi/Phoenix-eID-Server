"""Normative identifiers used by TR-03130-1 and TR-03124-1."""

EID_NS = "http://bsi.bund.de/eID/"
ECARD_NS = "http://www.bsi.bund.de/ecard/api/1.1"
DSS_NS = "urn:oasis:names:tc:dss:1.0:core:schema"
ISO_NS = "urn:iso:std:iso-iec:24727:tech:schema"
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

RESULT_MAJOR_OK = f"{ECARD_NS}/resultmajor#ok"
RESULT_MAJOR_ERROR = f"{ECARD_NS}/resultmajor#error"
RESULT_MINOR = "http://www.bsi.bund.de/eid/server/2.0/resultminor"

PAOS_BINDING = "urn:liberty:paos:2006-08"
PSK_PROTOCOL = "urn:ietf:rfc:4279"

ATTRIBUTE_NAMES = (
    "DocumentType",
    "IssuingState",
    "DateOfExpiry",
    "GivenNames",
    "FamilyNames",
    "ArtisticName",
    "AcademicTitle",
    "DateOfBirth",
    "PlaceOfBirth",
    "Nationality",
    "BirthName",
    "PlaceOfResidence",
    "ResidencePermitI",
    "RestrictedID",
    "AgeVerification",
    "PlaceVerification",
)

EID_TYPES = ("eIDCard", "Smart-eID", "SECertified", "SEEndorsed")

LOA_ORDER = {
    "http://bsi.bund.de/eID/LoA/undefined": 0,
    "http://bsi.bund.de/eID/LoA/normal": 1,
    "http://bsi.bund.de/eID/LoA/substantiell": 2,
    "http://bsi.bund.de/eID/LoA/hoch": 3,
    "http://eidas.europa.eu/LoA/low": 1,
    "http://eidas.europa.eu/LoA/substantial": 2,
    "http://eidas.europa.eu/LoA/high": 3,
}
