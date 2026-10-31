"""Моделі та HTTP-контракт; усі записи вигадані."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.secure_note import NoteCreate


@pytest.mark.parametrize("text", ("x" * 4096, "я" * 2048, "  текст  "))
def test_accepted_text_is_preserved(text):
    assert NoteCreate(text=text).text == text


@pytest.mark.parametrize("payload", (
    {"text": ""}, {"text": " "}, {"text": "x" * 4097},
    {"text": "я" * 2049}, {"text": 42},
    {"text": "demo", "key": "do-not-accept"},
))
def test_invalid_note_input(payload):
    with pytest.raises(ValidationError):
        NoteCreate(**payload)


def test_unknown_student_is_not_found():
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/students/{uuid4()}/secure-notes/{uuid4()}"
        )
    assert response.status_code == 404


def make_note(client,student_data,text='  synthetic note  '):
    student=client.post('/api/v1/students',json=student_data).json()['id']
    base=f'/api/v1/students/{student}/secure-notes'
    response=client.post(base,json={'text':text})
    assert response.status_code==201
    return base,response.json()
def test_note_api_and_internal_storage(client,student_data):
    from uuid import UUID
    base,n=make_note(client,student_data)
    assert set(n)=={'id','student_id','algorithm'}
    assert client.get(base+'/'+n['id']).json()['text']=='  synthetic note  '
    assert client.get(base).json()==[n]
    internal=client.app.state.note_repository._items[UUID(n['id'])]
    assert not hasattr(internal,'text') and not hasattr(internal,'key')
    assert len(internal.tag)==16 and len(internal.nonce)==12
    other=client.post('/api/v1/students',json={**student_data,'email':'other@example.com'}).json()['id']
    assert client.get(f'/api/v1/students/{other}/secure-notes').json()==[]
    assert client.get(f'/api/v1/students/{other}/secure-notes/'+n['id']).status_code==404
def test_damaged_note_is_rejected_without_plaintext(client,student_data):
    from dataclasses import replace
    from uuid import UUID
    base,n=make_note(client,student_data);items=client.app.state.note_repository._items
    key=UUID(n['id']);items[key]=replace(items[key],tag=bytes(16))
    response=client.get(base+'/'+n['id'])
    assert response.status_code==500 and response.json()=={'detail':'Protected note unavailable'}
def test_nonce_limit_rejects_only_new_writes(client,student_data):
    from app.security.keys import create_process_key
    client.app.state.process_key=create_process_key(limit=2)
    base,n=make_note(client,student_data)
    assert client.post(base,json={'text':'second'}).status_code==201
    assert client.post(base,json={'text':'third'}).status_code==503
    assert client.get(base+'/'+n['id']).status_code==200
def test_benchmark_report_reader(tmp_path,monkeypatch,client):
    import json
    from app.api import crypto_lab
    source=crypto_lab.REPORT_PATH
    path=tmp_path/'report.json';monkeypatch.setattr(crypto_lab,'REPORT_PATH',path)
    url='/api/v1/lab/crypto/benchmark-results'
    assert client.get(url).status_code==404
    path.write_text('{');assert client.get(url).status_code==500
    path.write_bytes(source.read_bytes());assert client.get(url).status_code==200
