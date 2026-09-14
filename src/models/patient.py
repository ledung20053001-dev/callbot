from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PatientIdentityRecord(BaseModel):
    """Minimum patient data allowed into the identity-matching flow."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    patient_id: str = Field(validation_alias=AliasChoices("patient_id", "id"))
    full_name: str = Field(validation_alias=AliasChoices("full_name", "name"))
    dob: str = Field(validation_alias=AliasChoices("dob", "date_of_birth"))
    phone: str | None = Field(
        default=None,
        validation_alias=AliasChoices("phone", "phone_number"),
    )
