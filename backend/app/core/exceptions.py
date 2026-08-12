"""Custom exception types mapped to clean JSON error responses in main.py."""


class AppException(Exception):
    status_code = 400
    error = "bad_request"

    def __init__(self, detail: str, status_code: int | None = None, error: str | None = None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error is not None:
            self.error = error
        super().__init__(detail)


class NotFoundException(AppException):
    status_code = 404
    error = "not_found"


class ForbiddenException(AppException):
    status_code = 403
    error = "forbidden"


class ValidationException(AppException):
    status_code = 422
    error = "validation_error"


class InsufficientDataException(AppException):
    status_code = 422
    error = "insufficient_data"
