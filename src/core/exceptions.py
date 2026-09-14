class CallbotError(Exception):
    """Base exception for expected Callbot failures."""


class CallNotFoundError(CallbotError):
    """Raised when a call session does not exist."""


class CallAlreadyExistsError(CallbotError):
    """Raised when attempting to create a duplicate call session."""


class PrivacyViolationError(CallbotError):
    """Raised when protected data is requested before identity verification."""
