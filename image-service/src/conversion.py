from webptools import cwebp


def convert(input_path: str, output_path: str, bin_path: str, q: int = 85) -> tuple[bool, str | None]:
    result: dict = cwebp(
        input_image=input_path,
        output_image=output_path,
        option=f"-q {q}",
        logging="-v",
        bin_path=bin_path,
    )

    if result['exit_code'] != 0:
        status, error = False, result['stderr'].decode()
    else:
        status, error = True, None

    return status, error
