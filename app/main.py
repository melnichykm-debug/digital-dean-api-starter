from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.students import router as students_router
from app.repositories.student_repository import (
    DuplicateEmailError, InMemoryStudentRepository, StudentNotFoundError,
)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Digital Dean API", version="0.2.0",
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

    from app.security.keys import create_process_key
    from app.repositories.secure_note_repository import SecureNoteRepository
    from app.api.secure_notes import router as note_router
    from app.api.crypto_lab import router as crypto_router
    application.state.process_key = create_process_key()
    application.state.note_repository = SecureNoteRepository()
    application.include_router(note_router)
    application.include_router(crypto_router)
    application.include_router(students_router)
    return application


app = create_app()
