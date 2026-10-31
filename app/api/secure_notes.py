from uuid import UUID, uuid4
from fastapi import APIRouter, Request, HTTPException
from app.schemas.secure_note import NoteCreate,NoteMetadata,NoteRead
from app.repositories.secure_note_repository import EncryptedNote
from app.security.context import note_aad
from app.security.adapters import seal_bytes,open_bytes,CiphertextError
router=APIRouter(prefix='/api/v1/students',tags=['secure-notes'])
def metadata(n): return NoteMetadata(id=n.note_id,student_id=n.student_id,algorithm=n.algorithm)
@router.post('/{student_id}/secure-notes',status_code=201,response_model=NoteMetadata)
def create(student_id:UUID,payload:NoteCreate,request:Request):
    state=request.app.state; state.student_repository.get(student_id)
    k=state.process_key; nid=uuid4(); algorithm='AES-256-GCM'
    try: nonce=k.nonces.next()
    except RuntimeError: raise HTTPException(503,'Protected note unavailable') from None
    ct,tag=seal_bytes('cryptography',algorithm,k.key,nonce,payload.text.encode(),note_aad(student_id,nid,algorithm,k.key_id))
    n=EncryptedNote(1,student_id,nid,algorithm,'cryptography',k.key_id,nonce,ct,tag)
    state.note_repository.add(n); return metadata(n)
@router.get('/{student_id}/secure-notes',response_model=list[NoteMetadata])
def list_notes(student_id:UUID,request:Request):
    request.app.state.student_repository.get(student_id)
    return [metadata(n) for n in request.app.state.note_repository.list(student_id)]
@router.get('/{student_id}/secure-notes/{note_id}',response_model=NoteRead)
def read(student_id:UUID,note_id:UUID,request:Request):
    state=request.app.state; state.student_repository.get(student_id)
    try: n=state.note_repository.get(student_id,note_id)
    except KeyError: raise HTTPException(404,'Note not found') from None
    k=state.process_key
    try:
        if n.version!=1 or n.key_id!=k.key_id or n.note_id!=note_id: raise ValueError()
        text=open_bytes(n.backend,n.algorithm,k.key,n.nonce,n.ciphertext,n.tag,note_aad(student_id,note_id,n.algorithm,k.key_id)).decode()
    except (ValueError,CiphertextError,UnicodeError): raise HTTPException(500,'Protected note unavailable') from None
    return NoteRead(**metadata(n).model_dump(),text=text)
