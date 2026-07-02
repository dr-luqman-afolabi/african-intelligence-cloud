import uuid
from sqlalchemy import Column, String, Boolean, Text, DateTime, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True, default="World Bank")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
