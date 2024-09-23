from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import aioboto3

from backend.application.common.dtos import ImageObj
from backend.application.common.interfaces.file_storages import ImageFileManagerInterface
from backend.infrastructure.s3.config import S3Config

if TYPE_CHECKING:
    from types_aiobotocore_s3.client import S3Client  # noqa: F401


@dataclass(slots=True)
class ImageS3FileManager(ImageFileManagerInterface):
    config: S3Config

    async def persist(
        self,
        image: ImageObj,
        save_path: Path,
    ) -> None:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key,
        ) as s3:  # type: S3Client
            with image.source.open("rb") as f:
                await s3.upload_fileobj(
                    Fileobj=f,
                    Bucket=self.config.bucket,
                    Key=str(save_path),
                    ExtraArgs={"ContentType": image.mime},
                )

            # TODO: generate presigned url and return?
