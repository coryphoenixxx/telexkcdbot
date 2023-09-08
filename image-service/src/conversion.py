from webptools import cwebp, grant_permission

grant_permission()

bin_path = "cwebp"


def convert(input_path: str, output_path: str, quality: int = 85) -> tuple[bool, str | None]:
    result = cwebp(
        input_image=input_path,
        output_image=output_path,
        option=f"-q {quality}",
        logging="-v",
    )

    if result['exit_code'] != 0:
        status, error = False, result['stderr'].decode()
    else:
        status, error = True, None

    return status, error
