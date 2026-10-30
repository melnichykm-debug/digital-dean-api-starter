"""Сховище в пам'яті без залежності від HTTP або FastAPI."""
from threading import RLock
from uuid import UUID, uuid4

from app.schemas.student import AcademicStatus, StudentCreate, StudentRead, StudentUpdate


class StudentNotFoundError(LookupError):
    """Запис студента не знайдено."""


class DuplicateEmailError(ValueError):
    """Електронна адреса вже використовується."""


class InMemoryStudentRepository:
    def __init__(self) -> None:
        self._students: dict[UUID, StudentRead] = {}
        self._lock = RLock()

    def _check_email(self, email: str, *, exclude_id: UUID | None = None) -> None:
        normalized = email.casefold()
        if any(
            student.id != exclude_id and str(student.email).casefold() == normalized
            for student in self._students.values()
        ):
            raise DuplicateEmailError

    def create(self, payload: StudentCreate) -> StudentRead:
        with self._lock:
            self._check_email(str(payload.email))
            student = StudentRead(id=uuid4(), **payload.model_dump())
            self._students[student.id] = student
            return student.model_copy(deep=True)

    def list(self, *, academic_status: AcademicStatus | None = None) -> list[StudentRead]:
        with self._lock:
            return [
                student.model_copy(deep=True)
                for student in self._students.values()
                if academic_status is None or student.academic_status == academic_status
            ]

    def get(self, student_id: UUID) -> StudentRead:
        with self._lock:
            if student_id not in self._students:
                raise StudentNotFoundError
            return self._students[student_id].model_copy(deep=True)

    def update(self, student_id: UUID, payload: StudentUpdate) -> StudentRead:
        with self._lock:
            current = self.get(student_id)
            changes = payload.model_dump(exclude_unset=True)
            if "email" in changes:
                self._check_email(str(changes["email"]), exclude_id=student_id)
            updated = StudentRead.model_validate({**current.model_dump(), **changes})
            self._students[student_id] = updated
            return updated.model_copy(deep=True)

    def clear(self) -> None:
        with self._lock:
            self._students.clear()
