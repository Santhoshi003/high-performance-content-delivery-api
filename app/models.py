import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    BigInteger,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


# ----------------------------------
# Asset (Mutable Content)
# ----------------------------------
class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_storage_key = Column(String, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    etag = Column(String, nullable=False)
    is_private = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    versions = relationship("AssetVersion", back_populates="asset")
    tokens = relationship("AccessToken", back_populates="asset")


# ----------------------------------
# AssetVersion (Immutable Content)
# ----------------------------------
class AssetVersion(Base):
    __tablename__ = "asset_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    object_storage_key = Column(String, unique=True, nullable=False)
    etag = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    asset = relationship("Asset", back_populates="versions")


# ----------------------------------
# AccessToken (Private Access)
# ----------------------------------
class AccessToken(Base):
    __tablename__ = "access_tokens"

    token = Column(String, primary_key=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    asset = relationship("Asset", back_populates="tokens")
