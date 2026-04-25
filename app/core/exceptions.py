class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str):
        super().__init__(status_code=404, message=message)


class BadRequestException(AppException):
    def __init__(self, message: str):
        super().__init__(status_code=400, message=message)


class UnauthorizedException(AppException):
    def __init__(self, message: str):
        super().__init__(status_code=401, message=message)


class ForbiddenException(AppException):
    def __init__(self, message: str):
        super().__init__(status_code=403, message=message)
