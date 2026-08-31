"""Protocol errors with the exact TR-03130 ResultMinor mapping."""

from dataclasses import dataclass

from .constants import RESULT_MINOR


@dataclass(slots=True)
class EIDError(Exception):
    operation: str
    code: str
    message: str

    @property
    def result_minor(self) -> str:
        return f"{RESULT_MINOR}/{self.operation}#{self.code}"

    def __str__(self) -> str:
        return self.message


def common(code: str, message: str) -> EIDError:
    return EIDError("common", code, message)


def use_id(code: str, message: str) -> EIDError:
    return EIDError("useID", code, message)


def get_result(code: str, message: str) -> EIDError:
    return EIDError("getResult", code, message)
