class CustomError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class NotFoundError(CustomError):
    ...


class AlreadyExistsError(CustomError):
    ...


class SameTextInfoError(CustomError):
    ...


class InvalidLanguageError(CustomError):
    ...


class InvalidImageExtensionError(CustomError):
    ...


class BigSizeError(CustomError):
    ...
