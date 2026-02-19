import uuid
import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Request,
    Response,
)
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.models import Base, Asset, AssetVersion, AccessToken
from app.storage import s3, BUCKET_NAME

app = FastAPI()

Base.metadata.create_all(bind=engine)


# ---------------------------------------
# Database Dependency
# ---------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------
# Health Check
# ---------------------------------------
@app.get("/")
def read_root():
    return {"message": "Content Delivery API running 🚀"}


# ---------------------------------------
# Upload Asset
# ---------------------------------------
@app.post("/assets/upload")
async def upload_asset(file: UploadFile = File(...), db: Session = Depends(get_db)):

    content = await file.read()
    etag = hashlib.sha256(content).hexdigest()

    asset_id = uuid.uuid4()
    object_key = f"{asset_id}_{file.filename}"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
        Body=content,
        ContentType=file.content_type,
    )

    new_asset = Asset(
        id=asset_id,
        object_storage_key=object_key,
        filename=file.filename,
        mime_type=file.content_type,
        size_bytes=len(content),
        etag=etag,
        is_private=False,
    )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return {
        "id": str(new_asset.id),
        "filename": new_asset.filename,
        "etag": new_asset.etag,
        "size": new_asset.size_bytes,
    }


# ---------------------------------------
# GET Download (Mutable)
# ---------------------------------------
@app.get("/assets/{asset_id}/download")
def download_asset(asset_id: str, request: Request, db: Session = Depends(get_db)):

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Conditional GET support
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == asset.etag:
        return Response(status_code=304)

    file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=asset.object_storage_key)
    file_content = file_obj["Body"].read()

    headers = {
        "ETag": asset.etag,
        "Cache-Control": "public, s-maxage=3600, max-age=60",
        "Last-Modified": asset.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "Content-Disposition": f'inline; filename="{asset.filename}"',
    }

    return Response(
        content=file_content,
        media_type=asset.mime_type,
        headers=headers,
    )


# ---------------------------------------
# HEAD Download (Mutable)
# ---------------------------------------
@app.head("/assets/{asset_id}/download")
def head_asset(asset_id: str, db: Session = Depends(get_db)):

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    headers = {
        "ETag": asset.etag,
        "Cache-Control": "public, s-maxage=3600, max-age=60",
        "Last-Modified": asset.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "Content-Length": str(asset.size_bytes),
        "Content-Type": asset.mime_type,
    }

    return Response(status_code=200, headers=headers)


# ---------------------------------------
# Publish Immutable Version
# ---------------------------------------
@app.post("/assets/{asset_id}/publish")
def publish_asset(asset_id: str, db: Session = Depends(get_db)):

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    version = AssetVersion(
        asset_id=asset.id,
        object_storage_key=asset.object_storage_key,
        etag=asset.etag,
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return {
        "version_id": str(version.id),
        "asset_id": str(asset.id),
        "etag": version.etag,
    }


# ---------------------------------------
# GET Immutable Public Endpoint
# ---------------------------------------
@app.get("/assets/public/{version_id}")
def get_public_version(version_id: str, db: Session = Depends(get_db)):

    version = db.query(AssetVersion).filter(
        AssetVersion.id == version_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=version.object_storage_key)
    file_content = file_obj["Body"].read()

    headers = {
        "ETag": version.etag,
        "Cache-Control": "public, max-age=31536000, immutable",
        "Last-Modified": version.created_at.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        ),
    }

    return Response(
        content=file_content,
        media_type="application/octet-stream",
        headers=headers,
    )


# ---------------------------------------
# HEAD Immutable Public Endpoint (IMPORTANT FIX)
# ---------------------------------------
@app.head("/assets/public/{version_id}")
def head_public_version(version_id: str, db: Session = Depends(get_db)):

    version = db.query(AssetVersion).filter(
        AssetVersion.id == version_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    headers = {
        "ETag": version.etag,
        "Cache-Control": "public, max-age=31536000, immutable",
        "Last-Modified": version.created_at.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        ),
    }

    return Response(status_code=200, headers=headers)


# ---------------------------------------
# Generate Access Token
# ---------------------------------------
@app.post("/assets/{asset_id}/generate-token")
def generate_access_token(asset_id: str, db: Session = Depends(get_db)):

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    token_value = secrets.token_urlsafe(32)
    expiration_time = datetime.utcnow() + timedelta(minutes=5)

    token = AccessToken(
        token=token_value,
        asset_id=asset.id,
        expires_at=expiration_time,
    )

    db.add(token)
    db.commit()

    return {
        "token": token_value,
        "expires_at": expiration_time,
    }


# ---------------------------------------
# Private Asset Endpoint
# ---------------------------------------
@app.get("/assets/private/{token}")
def get_private_asset(token: str, db: Session = Depends(get_db)):

    token_record = db.query(AccessToken).filter(
        AccessToken.token == token
    ).first()

    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid token")

    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Token expired")

    asset = db.query(Asset).filter(
        Asset.id == token_record.asset_id
    ).first()

    file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=asset.object_storage_key)
    file_content = file_obj["Body"].read()

    headers = {
        "Cache-Control": "private, no-store, no-cache, must-revalidate",
        "ETag": asset.etag,
        "Last-Modified": asset.created_at.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        ),
    }

    return Response(
        content=file_content,
        media_type=asset.mime_type,
        headers=headers,
    )
