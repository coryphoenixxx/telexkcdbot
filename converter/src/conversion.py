from webptools import cwebp

from src.helpers import ConversionError


def convert_to_webp(
        input_path: str,
        output_path: str,
        bin_dir: dict,
        extension: str,
        quality: int,
):
    result: dict = cwebp(
        input_image=input_path,
        output_image=output_path,
        option=f"-q {quality}",
        bin_path=bin_dir.get('gif2webp') if extension == 'gif' else bin_dir.get('cwebp'),
    )

    if result['exit_code'] != 0:
        # TODO: log: image name, error msg
        raise ConversionError(message=result['stderr'].decode().strip())
