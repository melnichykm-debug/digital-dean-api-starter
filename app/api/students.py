from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.repositories.student_repository import InMemoryStudentRepository
from app.schemas.error import ErrorResponse
from app.schemas.student import AcademicStatus, StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/api/v1/students", tags=["students"])


def get_repository(request: Request) -> InMemoryStudentRepository:
    return request.app.state.student_repository


Repository = Annotated[InMemoryStudentRepository, Depends(get_repository)]
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Студента не знайдено"}}
CONFLICT = {409: {"model": ErrorResponse, "description": "Email уже використовується"}}


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED, responses=CONFLICT)
def create_student(payload: StudentCreate, response: Response, repository: Repository) -> StudentRead:
    """Створити студента з новим серверним UUID."""
    student = repository.create(payload)
    response.headers["Location"] = f"/api/v1/students/{student.id}"
    return student


@router.get("", response_model=list[StudentRead])
def list_students(repository: Repository, academic_status: AcademicStatus | None = None) -> list[StudentRead]:
    """Повернути список або точний збіг за academic_status."""
    return repository.list(academic_status=academic_status)


@router.get("/{student_id}", response_model=StudentRead, responses=NOT_FOUND)
def get_student(student_id: UUID, repository: Repository) -> StudentRead:
    return repository.get(student_id)


@router.patch("/{student_id}", response_model=StudentRead, responses={**NOT_FOUND, **CONFLICT})
def update_student(student_id: UUID, payload: StudentUpdate, repository: Repository) -> StudentRead:
    """Змінити тільки передані дозволені поля; {} та null відхиляються."""
    return repository.update(student_id, payload)
