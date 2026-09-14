from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from src.core.exceptions import CallNotFoundError, PrivacyViolationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CallNotFoundError)
    async def call_not_found_handler(_request: Request, exc: CallNotFoundError) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "CALL_NOT_FOUND", "detail": str(exc)},
        )

    @app.exception_handler(PrivacyViolationError)
    async def privacy_violation_handler(
        _request: Request, _exc: PrivacyViolationError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": "IDENTITY_REQUIRED",
                "detail": "Identity verification is required.",
            },
        )
