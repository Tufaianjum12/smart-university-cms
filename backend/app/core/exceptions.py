"""
Small set of custom application exceptions.

Nothing raises these yet in Phase 1 (there's no business logic to fail),
but the pattern is established now: routers/services raise a specific,
named exception, and a global handler (registered in main.py) turns it
into a consistent JSON error response. This is what Phase 3+ will build
on instead of ad hoc HTTPException calls scattered everywhere.
"""


class AppError(Exception):
    """Base class for all application-specific errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message, status_code=403)
