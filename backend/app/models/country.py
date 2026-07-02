import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iso3 = Column(String(3), nullable=False, unique=True, index=True)
    iso2 = Column(String(2), nullable=True)
    name = Column(String(255), nullable=False)
    region = Column(String(100), nullable=True)
    income_group = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
