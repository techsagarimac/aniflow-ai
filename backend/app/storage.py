from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

ALLOWED_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/svg+xml",
    "application/pdf",
    "text/plain",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "video/mp4",
    "video/webm",
    "application/json",
}
MAX_BYTES = 25 * 1024 * 1024


class StorageService(ABC):
    @abstractmethod
    def save(self, *, relative_dir: str, filename: str, data: bytes) -> str: ...

    @abstractmethod
    def read(self, storage_path: str) -> bytes: ...

    @abstractmethod
    def absolute_path(self, storage_path: str) -> Path: ...


class LocalStorageService(StorageService):
    def __init__(self) -> None:
        self.root = get_settings().resolved_storage_dir

    def save(self, *, relative_dir: str, filename: str, data: bytes) -> str:
        folder = self.root / relative_dir
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_bytes(data)
        return str(path.relative_to(self.root))

    def read(self, storage_path: str) -> bytes:
        return self.absolute_path(storage_path).read_bytes()

    def absolute_path(self, storage_path: str) -> Path:
        path = (self.root / storage_path).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise HTTPException(status_code=400, detail="Invalid storage path")
        return path


storage = LocalStorageService()


async def read_validated_upload(file: UploadFile) -> tuple[bytes, str]:
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {content_type} is not allowed",
        )
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 25MB limit",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    return data, content_type
