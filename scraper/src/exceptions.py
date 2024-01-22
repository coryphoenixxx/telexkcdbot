from dataclasses import dataclass


@dataclass
class UnexpectedStatusCodeError(Exception):
    status: int


@dataclass
class ResourceIsUnavailableError(Exception):
    message: str
    retry_num: int
    interval: int
    last_response_status: int
