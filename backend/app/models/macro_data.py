from sqlalchemy import Column, Float, Integer, String, DateTime, UniqueConstraint, Index, Uuid, JSON
from sqlalchemy.sql import func
import uuid
from app.database import Base


class MacroData(Base):
    __tablename__ = "macro_data"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_iso3 = Column(String(3), nullable=False, index=True)
    indicator_code = Column(String(255), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    value = Column(Float, nullable=True)
    unit = Column(String(100))
    data_source = Column(String(255))
    source_id = Column(String(100), index=True)
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("country_iso3", "indicator_code", "year", name="uq_macro_data"),
        Index("ix_macro_data_country_indicator_year", "country_iso3", "indicator_code", "year"),
    )
