from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_role
from ..backup import build_backup_json, backup_filename, upload_to_s3
from ..database import get_db

router = APIRouter(prefix="/admin/backup", tags=["admin"])


@router.get("/local")
def download_local_backup(
    staff=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Streams a full JSON snapshot of every table as a file download —
    this is the 'local' backup: it lands wherever the browser saves
    downloads on whoever clicked the button's own machine."""
    data = build_backup_json()
    filename = backup_filename()

    db.add(models.BackupLog(
        destination=models.BackupDestination.local,
        status=models.BackupStatus.success,
        filename=filename,
        size_bytes=len(data),
        triggered_by=staff.username,
    ))
    db.commit()

    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/cloud", response_model=schemas.CloudBackupResult)
def push_cloud_backup(
    staff=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Builds the same snapshot and uploads it to configured S3-compatible
    storage. Returns a clear error (not a 500) if cloud storage isn't set
    up yet, so the dashboard can show it directly."""
    data = build_backup_json()
    filename = backup_filename()

    try:
        location = upload_to_s3(data, filename)
    except Exception as e:
        db.add(models.BackupLog(
            destination=models.BackupDestination.cloud,
            status=models.BackupStatus.failed,
            filename=filename,
            size_bytes=len(data),
            triggered_by=staff.username,
            error_message=str(e),
        ))
        db.commit()
        return schemas.CloudBackupResult(ok=False, detail=str(e))

    db.add(models.BackupLog(
        destination=models.BackupDestination.cloud,
        status=models.BackupStatus.success,
        filename=filename,
        size_bytes=len(data),
        triggered_by=staff.username,
    ))
    db.commit()
    return schemas.CloudBackupResult(ok=True, detail=f"Uploaded to {location}", filename=filename)


@router.get("/history", response_model=list[schemas.BackupLogOut])
def backup_history(
    staff=Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(models.BackupLog)
        .order_by(models.BackupLog.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        schemas.BackupLogOut(
            id=l.id, destination=l.destination.value, status=l.status.value,
            filename=l.filename, size_bytes=l.size_bytes, triggered_by=l.triggered_by,
            error_message=l.error_message, created_at=l.created_at,
        )
        for l in logs
    ]
