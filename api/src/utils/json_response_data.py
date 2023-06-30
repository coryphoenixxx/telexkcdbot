from dataclasses import dataclass, asdict


@dataclass
class SuccessJSONData:
    status: str = "success"
    message: str = None
    data: dict | list = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ErrorJSONData:
    status: str = "error"
    message: str = None
    data: dict | list = None

    def to_dict(self):
        return asdict(self)
