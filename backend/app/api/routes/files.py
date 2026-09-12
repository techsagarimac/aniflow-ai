from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.enums import FileKind, ReviewStatus, RevisionStatus, UserRole
from app.models.files import FileAsset, FileVersion, RevisionRequest
from app.models.production import Episode, Scene
from app.models.user import User
from app.schemas import FileVersionOut
from app.services.serializers import file_version_out
from app.storage import read_validated_upload, storage

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/scene/{scene_id}", response_model=list[FileVersionOut])
def list_versions(scene_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    versions = db.scalars(
        select(FileVersion)
        .options(selectinload(FileVersion.artist))
        .where(FileVersion.scene_id == scene_id)
        .order_by(FileVersion.version_number)
    ).all()
    return [file_version_out(v) for v in versions]


@router.post("/scene/{scene_id}", response_model=FileVersionOut, status_code=201)
async def upload_version(
    scene_id: int,
    upload: UploadFile = File(...),
    notes: str = Form(""),
    kind: FileKind = Form(FileKind.SCENE_RENDER),
    mark_final: bool = Form(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scene = db.get(Scene, scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    if user.role == UserRole.ARTIST and scene.assigned_artist_id != user.id:
        raise HTTPException(403, "Artists can only upload to assigned scenes")

    data, content_type = await read_validated_upload(upload)
    episode = db.get(Episode, scene.episode_id)
    asset = db.scalar(select(FileAsset).where(FileAsset.scene_id == scene_id))
    if asset is None:
        asset = FileAsset(
            project_id=episode.project_id if episode else None,
            scene_id=scene_id,
            kind=kind,
            original_name=upload.filename or "upload",
            uploaded_by_id=user.id,
        )
        db.add(asset)
        db.flush()

    last = db.scalar(
        select(FileVersion)
        .where(FileVersion.file_id == asset.id)
        .order_by(FileVersion.version_number.desc())
    )
    next_num = (last.version_number + 1) if last else 1
    label = "final" if mark_final else f"v{next_num:02d}"
    ext = (upload.filename or "file").split(".")[-1]
    stored_name = f"scene_{scene.scene_number:03d}_{label}.{ext}"
    path = storage.save(relative_dir=f"scenes/{scene_id}", filename=stored_name, data=data)
    version = FileVersion(
        file_id=asset.id,
        scene_id=scene_id,
        version_number=next_num,
        label=label,
        storage_path=path,
        mime_type=content_type,
        size_bytes=len(data),
        notes=notes,
        artist_id=user.id,
        review_status=ReviewStatus.PENDING,
    )
    db.add(version)
    open_revs = db.scalars(
        select(RevisionRequest).where(
            RevisionRequest.scene_id == scene_id,
            RevisionRequest.status.in_([RevisionStatus.OPEN, RevisionStatus.IN_PROGRESS]),
        )
    ).all()
    for rev in open_revs:
        rev.status = RevisionStatus.IN_PROGRESS
    db.commit()
    version = db.scalar(
        select(FileVersion).options(selectinload(FileVersion.artist)).where(FileVersion.id == version.id)
    )
    return file_version_out(version)


@router.get("/versions/{version_id}/download")
def download_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    version = db.get(FileVersion, version_id)
    if not version:
        raise HTTPException(404, "Version not found")
    path = storage.absolute_path(version.storage_path)
    if not path.exists():
        raise HTTPException(404, "File missing on disk")
    return FileResponse(path, media_type=version.mime_type, filename=path.name)
