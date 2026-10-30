from uuid import UUID, uuid4

import pytest

BASE = "/api/v1/students"


def create(client, student_data, **changes):
    response = client.post(BASE, json={**student_data, **changes})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_server_uuid_and_fields(client, student_data):
    response = client.post(BASE, json=student_data)
    assert response.status_code == 201
    body = response.json()
    assert UUID(body["id"]).version == 4
    assert {key: value for key, value in body.items() if key != "id"} == student_data
    assert response.headers["location"] == f"{BASE}/{body['id']}"


def test_empty_list(client):
    assert client.get(BASE).json() == []


def test_list_and_get(client, student_data):
    first = create(client, student_data)
    second = create(client, student_data, email="second@example.com")
    response = client.get(BASE)
    assert response.status_code == 200
    assert response.json() == [first, second]
    assert first["id"] != second["id"]
    response = client.get(f"{BASE}/{first['id']}")
    assert response.status_code == 200
    assert response.json() == first


@pytest.mark.parametrize("method", ["get", "patch"])
def test_missing_student_is_controlled(client, method):
    kwargs = {"json": {"group_code": "КН-32"}} if method == "patch" else {}
    response = getattr(client, method)(f"{BASE}/{uuid4()}", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": {
        "code": "student_not_found", "message": "Студента не знайдено",
    }}
    assert "Traceback" not in response.text


@pytest.mark.parametrize("method", ["get", "patch"])
def test_invalid_uuid(client, method):
    kwargs = {"json": {"group_code": "КН-32"}} if method == "patch" else {}
    response = getattr(client, method)(f"{BASE}/not-a-uuid", **kwargs)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "student_id"]


@pytest.mark.parametrize("field,value", [
    ("email", "not-an-email"), ("full_name", "  абвг  "),
    ("full_name", "а" * 121), ("group_code", "кн-31"),
    ("group_code", "КН-3"), ("group_code", "КН-311"),
    ("group_code", "КН-31\nEXTRA"), ("group_code", "Ы-31"),
    ("academic_status", "unknown"), ("academic_status", 1),
])
def test_invalid_create_has_no_side_effect(client, student_data, field, value):
    response = client.post(BASE, json={**student_data, field: value})
    assert response.status_code == 422
    assert client.get(BASE).json() == []


@pytest.mark.parametrize("field", ["full_name", "email", "group_code", "academic_status"])
def test_missing_or_null_create_field(client, student_data, field):
    data = dict(student_data)
    data.pop(field)
    assert client.post(BASE, json=data).status_code == 422
    assert client.post(BASE, json={**student_data, field: None}).status_code == 422
    assert client.get(BASE).json() == []


@pytest.mark.parametrize("name", ["а" * 5, "а" * 120])
def test_name_boundaries_and_trim(client, student_data, name):
    body = create(client, student_data, full_name=f"  {name}  ")
    assert body["full_name"] == name


@pytest.mark.parametrize("group", ["КН-31", "CS-09", "ІПЗ2-00", "ҐЄЇ-99"])
def test_group_alphabet(client, student_data, group):
    assert create(client, student_data, group_code=f" {group} ")["group_code"] == group


@pytest.mark.parametrize("extra", [{"is_admin": True}, {"id": str(uuid4())}])
def test_create_forbids_server_or_unknown_fields(client, student_data, extra):
    response = client.post(BASE, json={**student_data, **extra})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"
    assert client.get(BASE).json() == []


def test_duplicate_email_case_insensitive_on_create(client, student_data):
    create(client, student_data)
    response = client.post(BASE, json={**student_data, "email": "OLENA.KOVAL@EXAMPLE.COM"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "duplicate_email"
    assert len(client.get(BASE).json()) == 1


@pytest.mark.parametrize("field,value", [
    ("group_code", "КН-32"), ("full_name", "Ірина Тестова"),
    ("email", "updated@example.com"), ("academic_status", "academic_leave"),
])
def test_patch_changes_only_supplied_field(client, student_data, field, value):
    before = create(client, student_data)
    response = client.patch(f"{BASE}/{before['id']}", json={field: value})
    assert response.status_code == 200
    assert response.json() == {**before, field: value}
    assert client.get(f"{BASE}/{before['id']}").json() == response.json()


@pytest.mark.parametrize("patch", [
    {}, {"is_admin": True}, {"id": str(uuid4())},
    {"full_name": None}, {"email": None}, {"group_code": None}, {"academic_status": None},
    {"group_code": "КН-32", "is_admin": True},
    {"email": "bad"}, {"academic_status": "unknown"},
])
def test_invalid_patch_does_not_modify_record(client, student_data, patch):
    before = create(client, student_data)
    response = client.patch(f"{BASE}/{before['id']}", json=patch)
    assert response.status_code == 422
    assert client.get(f"{BASE}/{before['id']}").json() == before


def test_patch_email_conflict_is_atomic_and_self_email_allowed(client, student_data):
    first = create(client, student_data)
    second = create(client, student_data, email="second@example.com")
    response = client.patch(f"{BASE}/{second['id']}", json={
        "email": first["email"].upper(), "group_code": "КН-32",
    })
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "duplicate_email"
    assert client.get(f"{BASE}/{second['id']}").json() == second
    response = client.patch(f"{BASE}/{first['id']}", json={"email": first["email"]})
    assert response.status_code == 200
    assert response.json() == first


@pytest.mark.parametrize("status", ["active", "academic_leave", "graduated", "expelled"])
def test_variant_accepts_each_status_and_filters(client, student_data, status):
    target = create(client, student_data, academic_status=status)
    other = "graduated" if status == "active" else "active"
    create(client, student_data, email="other@example.com", academic_status=other)
    response = client.get(BASE, params={"academic_status": status})
    assert response.status_code == 200
    assert response.json() == [target]


def test_filter_tracks_updated_status_and_empty_result(client, student_data):
    student = create(client, student_data)
    assert client.get(BASE, params={"academic_status": "expelled"}).json() == []
    assert client.patch(f"{BASE}/{student['id']}", json={"academic_status": "graduated"}).status_code == 200
    assert client.get(BASE, params={"academic_status": "active"}).json() == []
    assert len(client.get(BASE, params={"academic_status": "graduated"}).json()) == 1


@pytest.mark.parametrize("value", ["unknown", "", "ACTIVE", "null"])
def test_variant_rejects_unknown_filter(client, value):
    response = client.get(BASE, params={"academic_status": value})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "academic_status"]


def test_malformed_json_is_rejected(client):
    response = client.post(BASE, content='{"full_name":', headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"
    assert client.get(BASE).json() == []


def test_openapi_contract_and_docs(client):
    assert client.get("/docs").status_code == 200
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    models = schema["components"]["schemas"]
    assert models["AcademicStatus"]["enum"] == ["active", "academic_leave", "graduated", "expelled"]
    assert models["StudentCreate"]["additionalProperties"] is False
    assert "id" not in models["StudentCreate"]["properties"]
    assert "id" not in models["StudentUpdate"]["properties"]
    assert "id" in models["StudentRead"]["required"]
    assert "patch" in schema["paths"][f"{BASE}/{{student_id}}"]
    assert "delete" not in schema["paths"][f"{BASE}/{{student_id}}"]
