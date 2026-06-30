import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Uuid, Text
from sqlalchemy.sql import func
from app.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), nullable=False, unique=True, index=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(255), nullable=False)
    access_method = Column(Text, nullable=False)
    # A = Open API, B = Open downloadable, C = Restricted microdata, D = Client-owned
    license_category = Column(String(1), nullable=False)
    update_frequency = Column(String(100), nullable=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    redistribution_allowed = Column(Boolean, nullable=False, default=True)
    citation_required = Column(Boolean, nullable=False, default=True)
    data_owner = Column(String(255), nullable=False)
    # live | planned | user_upload | deprecated
    connector_status = Column(String(50), nullable=False, default="planned")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
