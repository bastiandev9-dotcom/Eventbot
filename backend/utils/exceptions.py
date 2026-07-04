"""
Custom Exceptions
=================
Exception classes untuk EventBot.
"""


class EventBotException(Exception):
    """Base exception untuk EventBot."""
    pass


class ValidationError(EventBotException):
    """Exception untuk validation error."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class NotFoundError(EventBotException):
    """Exception untuk data not found."""
    def __init__(self, resource: str, identifier: str = None):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource} tidak ditemukan"
        if identifier:
            message += f" ({identifier})"
        super().__init__(message)


class AuthenticationError(EventBotException):
    """Exception untuk authentication error."""
    pass


class AuthorizationError(EventBotException):
    """Exception untuk authorization error (tidak punya akses)."""
    pass


class DatabaseError(EventBotException):
    """Exception untuk database error."""
    pass