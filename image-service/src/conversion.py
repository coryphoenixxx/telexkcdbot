from webptools import cwebp


def convert_to_webp(
        input_path: str,
        output_path: str,
        bin_dir: dict,
        extension: str,
        quality: int,
) -> tuple[bool, str | None]:
    result: dict = cwebp(
        input_image=input_path,
        output_image=output_path,
        option=f"-q {quality}",
        logging="-v",
        bin_path=bin_dir.get('gif2webp') if extension == 'gif' else bin_dir.get('cwebp'),
    )

    if result['exit_code'] != 0:
        status, error = False, result['stderr'].decode()
    else:
        status, error = True, None

    return status, error
