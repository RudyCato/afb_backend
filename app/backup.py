"""
Database backup: exports every table to a single JSON snapshot.

Deliberately framework-light — no pg_dump dependency (not available on
Render's free tier without shell access), just SQLAlchemy reading every
row of every model and serializing it. Restoring from this file means
writing a small loader script when the day comes; this module only
covers taking the backup, not restoring it.
"""
import io
import json
import os
from datetime import datetime, date

from sqlalchemy import inspect

from . import models
from .database import Base, SessionLocal

# Every mapped table gets backed up automatically — new models added later
# are included without needing to touch this file.
_ALL_MODELS = [
    cls for cls in vars(models).values()
    if isinstance(cls, type) and issubclass(cls, Base) and cls is not Base
]


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):  # enum members
        return value.value
    return value


def build_backup_json() -> bytes:
    """Returns the full backup as UTF-8 JSON bytes, plus row counts."""
    db = SessionLocal()
    try:
        snapshot = {
            "generated_at": datetime.utcnow().isoformat(),
            "tables": {},
        }
        for model_cls in _ALL_MODELS:
            table_name = model_cls.__tablename__
            columns = [c.key for c in inspect(model_cls).columns]
            rows = db.query(model_cls).all()
            snapshot["tables"][table_name] = [
                {col: _serialize_value(getattr(row, col)) for col in columns}
                for row in rows
            ]
        payload = json.dumps(snapshot, indent=2).encode("utf-8")
        return payload
    finally:
        db.close()


def backup_filename() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"afb-backup-{stamp}.json"


def upload_to_s3(data: bytes, filename: str):
    """
    Uploads to any S3-compatible bucket (AWS S3, Backblaze B2, Cloudflare R2,
    DigitalOcean Spaces). Configured entirely via env vars — raises a plain
    RuntimeError with a clear message if it isn't set up yet, rather than a
    boto3 stack trace.
    """
    bucket = os.environ.get("BACKUP_S3_BUCKET")
    if not bucket:
        raise RuntimeError(
            "Cloud backup isn't configured yet. Set BACKUP_S3_BUCKET, "
            "BACKUP_S3_ACCESS_KEY_ID, and BACKUP_S3_SECRET_ACCESS_KEY as "
            "environment variables (BACKUP_S3_ENDPOINT_URL and "
            "BACKUP_S3_REGION are optional, for non-AWS S3-compatible "
            "storage like Backblaze B2 or Cloudflare R2)."
        )

    access_key = os.environ.get("BACKUP_S3_ACCESS_KEY_ID")
    secret_key = os.environ.get("BACKUP_S3_SECRET_ACCESS_KEY")
    if not access_key or not secret_key:
        raise RuntimeError(
            "BACKUP_S3_BUCKET is set but BACKUP_S3_ACCESS_KEY_ID / "
            "BACKUP_S3_SECRET_ACCESS_KEY are missing."
        )

    import boto3  # imported lazily so the app still runs if boto3 isn't installed

    client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=os.environ.get("BACKUP_S3_REGION", "us-east-1"),
        endpoint_url=os.environ.get("BACKUP_S3_ENDPOINT_URL") or None,
    )
    key = f"afb-backups/{filename}"
    client.upload_fileobj(io.BytesIO(data), bucket, key)
    return f"s3://{bucket}/{key}"
