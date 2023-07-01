from dataclasses import dataclass, asdict


@dataclass
class BaseJSONData:
    message: str = None
    data: dict | list = None

    def to_dict(self):
        return asdict(self)


@dataclass
class SuccessJSONData(BaseJSONData):
    status: str = "success"


@dataclass
class ErrorJSONData(BaseJSONData):
    status: str = "error"
