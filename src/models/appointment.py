from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from src.models.patient import PatientIdentityRecord


class AppointmentIdentityContext(BaseModel):
    """Appointment projection restricted to fields needed for identity lookup."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    appointment_id: str = Field(validation_alias=AliasChoices("appointment_id", "id"))
    patient_id: str
    patient: PatientIdentityRecord | None = None
