from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.students import router as students_router
from app.repositories.student_repository import (
    DuplicateEmailError, InMemoryStudentRepository, StudentNotFoundError,
)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Digital Dean API", version="0.1.0",
        description="Практична робота 1. Номер у списку 15, варіант 3 — academic_status.",
    )
    application.state.student_repository = InMemoryStudentRepository()

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.exception_handler(StudentNotFoundError)
    async def not_found(request: Request, exc: StudentNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": {
            "code": "student_not_found", "message": "Студента не знайдено",
        }})

    @application.exception_handler(DuplicateEmailError)
    async def duplicate_email(request: Request, exc: DuplicateEmailError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": {
            "code": "duplicate_email", "message": "Електронна адреса вже використовується",
        }})

    application.include_router(students_router)
    return application


app = create_app()
