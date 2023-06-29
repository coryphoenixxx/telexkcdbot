from dataclasses import dataclass, asdict


@dataclass
class SuccessJSONData:
    data: dict | list
    status: str = "success"
    message: str = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ErrorJSONData:
    message: str
    status: str = "error"
    data: dict | list = None

    def to_dict(self):
        return asdict(self)
