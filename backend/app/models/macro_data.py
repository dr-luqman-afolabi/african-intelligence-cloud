import uuid
from sqlalchemy import Column, Float, Integer, String, ForeignKey, UniqueConstraint, Index, DateTime, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MacroData(Base):
    __tablename__ = "macro_data"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(Uuid(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    indicator_id = Column(Uuid(as_uuid=True), ForeignKey("indicators.id"), nullable=False)
    year = Column(Integer, nullable=False)
    value = Column(Float, nullable=True)
    data_source = Column(String(50), nullable=False, default="World Bank")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    country = relationship("Country", back_populates="macro_data")
    indicator = relationship("Indicator", back_populates="macro_data")

    __table_args__ = (
        UniqueConstraint("country_id", "indicator_id", "year", name="uq_macro_data"),
        Index("ix_macro_data_lookup", "country_id", "indicator_id", "year"),
    )
