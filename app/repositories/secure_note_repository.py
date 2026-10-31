"""Сховище зберігає конверт, не відкритий текст і не ключ."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class EncryptedNote:
    version: int
    student_id: UUID
    note_id: UUID
    algorithm: str
    backend: str
    key_id: UUID
    nonce: bytes
    ciphertext: bytes
    tag: bytes


class SecureNoteRepository:
    def __init__(self):
        self._items: dict[UUID, EncryptedNote] = {}

    def add(self,note):
        if note.note_id in self._items: raise ValueError('Duplicate note')
        self._items[note.note_id]=note
    def get(self,student_id,note_id):
        note=self._items[note_id]
        if note.student_id != student_id: raise KeyError(note_id)
        return note
    def list(self,student_id):
        return [n for n in self._items.values() if n.student_id==student_id]

    def clear(self) -> None:
        """Очищення записів не змінює ключ і не скидає його лічильник."""
        self._items.clear()


repository = SecureNoteRepository()

# TODO: додайте операції свого індивідуального варіанта.
# Підміна _items допустима лише в тестах, не через окремий HTTP-маршрут.
