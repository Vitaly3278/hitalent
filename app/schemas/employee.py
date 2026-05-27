from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import trim_non_empty


class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: date | None = None

    @field_validator("full_name", "position")
    @classmethod
    def validate_text_fields(cls, value: str, info) -> str:
        return trim_non_empty(value, info.field_name)


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime
