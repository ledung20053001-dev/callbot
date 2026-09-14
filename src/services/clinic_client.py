import re
from collections.abc import Mapping
from typing import Any, cast

import httpx
from pydantic import SecretStr, ValidationError

from src.config import Settings
from src.core.exceptions import (
    ClinicAPIError,
    ClinicAuthenticationError,
    ClinicContractError,
    ClinicNotFoundError,
)
from src.models.appointment import AppointmentIdentityContext
from src.models.patient import PatientIdentityRecord

PHONE_PATTERN = re.compile(r"^(02|03|05|07|08|09)\d{8}$")


class ClinicClient:
    """Async read client for identity-related Clinic Mock endpoints only."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: SecretStr | str | None,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        token = api_key.get_secret_value() if isinstance(api_key, SecretStr) else api_key
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "ClinicClient":
        return cls(
            base_url=settings.clinic_api_base_url,
            api_key=settings.clinic_api_key,
            timeout_seconds=settings.clinic_api_timeout_seconds,
        )

    async def __aenter__(self) -> "ClinicClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> bool:
        response = await self._request("GET", "/health")
        payload = self._json_object(response)
        return payload.get("status") == "ok"

    async def find_patients_by_phone(self, phone: str) -> list[PatientIdentityRecord]:
        """Return identity candidates; phone remains discovery metadata, not proof."""

        if not PHONE_PATTERN.fullmatch(phone):
            raise ValueError("Phone must be a valid 10-digit Vietnamese number.")
        response = await self._request("GET", "/v1/patients", params={"phone": phone})
        records = self._extract_collection(response, keys=("items", "patients", "data"))
        try:
            return [PatientIdentityRecord.model_validate(record) for record in records]
        except ValidationError as exc:
            raise ClinicContractError("Invalid patient identity payload.") from exc

    async def get_appointment_identity(
        self, appointment_id: str
    ) -> AppointmentIdentityContext:
        """Fetch an appointment but expose only its identity projection."""

        response = await self._request("GET", f"/v1/appointments/{appointment_id}")
        payload = self._json_object(response)
        candidate = payload.get("data", payload)
        if not isinstance(candidate, Mapping):
            raise ClinicContractError("Invalid appointment identity payload.")
        try:
            return AppointmentIdentityContext.model_validate(candidate)
        except ValidationError as exc:
            raise ClinicContractError("Invalid appointment identity payload.") from exc

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        if path.startswith("/_harness"):
            raise ClinicAPIError("Harness endpoints are forbidden.")
        try:
            response = await self._client.request(method, path, params=params)
        except httpx.TimeoutException as exc:
            raise ClinicAPIError("Clinic Mock request timed out.") from exc
        except httpx.RequestError as exc:
            raise ClinicAPIError("Clinic Mock connection failed.") from exc

        if response.status_code in (401, 403):
            raise ClinicAuthenticationError("Clinic Mock authentication failed.")
        if response.status_code == 404:
            raise ClinicNotFoundError("Clinic Mock resource was not found.")
        if response.is_error:
            raise ClinicAPIError(f"Clinic Mock returned HTTP {response.status_code}.")
        return response

    @staticmethod
    def _json_object(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ClinicContractError("Clinic Mock returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ClinicContractError("Clinic Mock returned an unexpected JSON shape.")
        return payload

    @classmethod
    def _extract_collection(
        cls,
        response: httpx.Response,
        *,
        keys: tuple[str, ...],
    ) -> list[Mapping[str, Any]]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ClinicContractError("Clinic Mock returned invalid JSON.") from exc

        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = None
            for key in keys:
                candidate = payload.get(key)
                if isinstance(candidate, list):
                    records = candidate
                    break
        else:
            raise ClinicContractError("Clinic Mock collection payload is invalid.")

        if records is None:
            raise ClinicContractError("Clinic Mock collection envelope is unknown.")
        if not all(isinstance(record, Mapping) for record in records):
            raise ClinicContractError("Clinic Mock collection contains invalid records.")
        return [cast(Mapping[str, Any], record) for record in records]
