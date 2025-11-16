class BasicAppError(Exception):
    status_code = 400
    error_code = "APP_ERROR"
    message = "Application Error"

    def __init__(self, message=None, *, error_code=None, status_code=None):
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code

        super().__init__(self.message)


class NotFoundError(BasicAppError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class UnauthorizedError(BasicAppError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Unauthorized"


class ForbiddenError(BasicAppError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Forbidden"


class ConflictError(BasicAppError):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource already exists"


class ServerError(BasicAppError):
    status_code = 500
    error_code = "SERVER_ERROR"
    message = "Server error"
