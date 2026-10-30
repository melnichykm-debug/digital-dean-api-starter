"""Контракт студента для варіанта 3 (15 % 4 = 3)."""
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, model_validator
from pydantic.json_schema import SkipJsonSchema


class AcademicStatus(StrEnum):
    """Явний навчальний перелік станів."""
    ACTIVE = "active"
    ACADEMIC_LEAVE = "academic_leave"
    GRADUATED = "graduated"
    EXPELLED = "expelled"


FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=120)]
GroupCode = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[A-ZА-ЩЬЮЯЄІЇҐ0-9]+-[0-9]{2}$"),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StudentCreate(StrictModel):
    full_name: FullName
    email: EmailStr
    group_code: GroupCode
    academic_status: AcademicStatus


class StudentRead(StudentCreate):
    id: UUID


class StudentUpdate(StrictModel):
    # Пропуск поля дозволений, явний null заборонений валідатором.
    # SkipJsonSchema прибирає null зі схеми OpenAPI.
    full_name: FullName | SkipJsonSchema[None] = None
    email: EmailStr | SkipJsonSchema[None] = None
    group_code: GroupCode | SkipJsonSchema[None] = None
    academic_status: AcademicStatus | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def require_nonempty_update(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Передайте хоча б одне дозволене поле")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Передані поля не можуть мати значення null")
        return self
