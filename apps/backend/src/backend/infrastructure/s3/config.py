from dataclasses import dataclass


@dataclass(slots=True)
class S3Config:
    bucket: str
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
