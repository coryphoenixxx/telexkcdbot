from dataclasses import dataclass


@dataclass(slots=True)
class DownloadError(Exception):
    url: str
    attempts: int
    interval: float

    @property
    def message(self) -> str:
        return f"Couldn't download the file from {self.url}"
