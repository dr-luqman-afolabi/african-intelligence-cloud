from pydantic import BaseModel
from uuid import UUID


class IndicatorResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    unit: str | None
    category: str | None
    source: str | None

    class Config:
        from_attributes = True
