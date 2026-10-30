import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    application = create_app()
    application.state.student_repository.clear()
    with TestClient(application) as test_client:
        yield test_client
    application.state.student_repository.clear()


@pytest.fixture
def student_data():
    return {
        "full_name": "Олена Коваль",
        "email": "olena.koval@example.com",
        "group_code": "КН-31",
        "academic_status": "active",
    }
