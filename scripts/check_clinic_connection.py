"""Check Clinic Mock connectivity without printing credentials or patient data."""

import argparse
import asyncio

from src.config import get_settings
from src.core.exceptions import ClinicAPIError
from src.services.clinic_client import ClinicClient


async def check(phone: str | None) -> int:
    settings = get_settings()
    async with ClinicClient.from_settings(settings) as client:
        try:
            healthy = await client.health_check()
            print(f"Clinic Mock health: {'OK' if healthy else 'UNEXPECTED'}")
            if phone:
                patients = await client.find_patients_by_phone(phone)
                print(f"Authenticated patient lookup: OK ({len(patients)} candidate(s))")
        except ClinicAPIError as exc:
            print(f"Clinic Mock check failed: {exc}")
            return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phone", help="Synthetic Vietnamese phone number to look up")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(check(args.phone)))


if __name__ == "__main__":
    main()
