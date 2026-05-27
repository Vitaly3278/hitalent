from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.employee import EmployeeRead
from app.schemas.validators import trim_non_empty


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return trim_non_empty(value, "name")


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return trim_non_empty(value, "name")


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime


class DepartmentTreeNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime
    employees: list[EmployeeRead] = []
    children: list["DepartmentTreeNode"] = []


class DepartmentDetail(BaseModel):
    department: DepartmentRead
    employees: list[EmployeeRead] = []
    children: list[DepartmentTreeNode] = []


DepartmentTreeNode.model_rebuild()
