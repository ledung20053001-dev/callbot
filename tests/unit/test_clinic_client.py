import httpx
import pytest
from pydantic import SecretStr

from src.core.exceptions import ClinicAuthenticationError
from src.services.clinic_client import ClinicClient


@pytest.mark.asyncio
async def test_find_patients_returns_identity_fields_only() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-secret"
        assert request.url.params["phone"] == "0900000000"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "patient-1",
                        "full_name": "Nguyễn Văn A",
                        "date_of_birth": "1978-03-14",
                        "phone": "0900000000",
                        "medical_record": "must-not-enter-identity-flow",
                    }
                ]
            },
        )

    async with ClinicClient(
        base_url="https://clinic.test",
        api_key=SecretStr("test-secret"),
        transport=httpx.MockTransport(handler),
    ) as client:
        patients = await client.find_patients_by_phone("0900000000")

    assert len(patients) == 1
    assert patients[0].patient_id == "patient-1"
    assert patients[0].full_name == "Nguyễn Văn A"
    assert patients[0].dob == "1978-03-14"
    assert "medical_record" not in patients[0].model_dump()


@pytest.mark.asyncio
async def test_appointment_response_is_reduced_to_identity_context() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "appointment_id": "apt-1",
                "patient_id": "patient-1",
                "clinic_name": "Protected clinic",
                "appointment_time": "09:00",
                "status": "SCHEDULED",
            },
        )

    async with ClinicClient(
        base_url="https://clinic.test",
        api_key="test-secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        context = await client.get_appointment_identity("apt-1")

    assert context.model_dump() == {
        "appointment_id": "apt-1",
        "patient_id": "patient-1",
        "patient": None,
    }


@pytest.mark.asyncio
async def test_invalid_phone_is_rejected_before_http_request() -> None:
    request_count = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json={"items": []})

    async with ClinicClient(
        base_url="https://clinic.test",
        api_key="test-secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ValueError):
            await client.find_patients_by_phone("invalid")

    assert request_count == 0


@pytest.mark.asyncio
async def test_authentication_failure_is_mapped_without_leaking_key() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"code": "UNAUTHORIZED"}})

    async with ClinicClient(
        base_url="https://clinic.test",
        api_key="do-not-leak",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ClinicAuthenticationError) as error:
            await client.find_patients_by_phone("0900000000")

    assert "do-not-leak" not in str(error.value)
