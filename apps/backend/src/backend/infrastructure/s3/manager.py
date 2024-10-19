from dataclasses import dataclass
from pathlib import Path

from types_aiobotocore_s3.client import S3Client

from backend.application.common.interfaces import ImageFileManagerInterface
from backend.domain.value_objects import ImageFileObj


@dataclass(slots=True)
class ImageS3FileManager(ImageFileManagerInterface):
    client: S3Client
    bucket: str

    async def save(
        self,
        image: ImageFileObj,
        save_path: Path,
    ) -> None:
        with image.source.open("rb") as f:
            await self.client.upload_fileobj(
                Fileobj=f,
                Bucket=self.bucket,
                Key=str(save_path),
                ExtraArgs={"ContentType": image.mime},
            )

    async def move(self, path_from: Path, path_to: Path) -> None:
        await self.client.copy(
            CopySource={
                "Bucket": self.bucket,
                "Key": str(path_from),
            },
            Bucket=self.bucket,
            Key=str(path_to),
        )
        await self.delete(path_from)

    async def delete(self, path: Path) -> None:
        await self.client.delete_object(Bucket=self.bucket, Key=str(path))
