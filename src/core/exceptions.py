class CallbotError(Exception):
    """Base exception for expected Callbot failures."""


class CallNotFoundError(CallbotError):
    """Raised when a call session does not exist."""


class CallAlreadyExistsError(CallbotError):
    """Raised when attempting to create a duplicate call session."""


class PrivacyViolationError(CallbotError):
    """Raised when protected data is requested before identity verification."""


class ClinicAPIError(CallbotError):
    """Raised when Clinic Mock cannot fulfill a request."""


class ClinicAuthenticationError(ClinicAPIError):
    """Raised when Clinic Mock rejects the configured bearer token."""


class ClinicNotFoundError(ClinicAPIError):
    """Raised when a requested Clinic Mock resource does not exist."""


class ClinicContractError(ClinicAPIError):
    """Raised when Clinic Mock returns an unexpected payload shape."""
