from pydantic import BaseModel
from uuid import UUID


class CountryResponse(BaseModel):
    id: UUID
    iso3: str
    iso2: str | None
    name: str
    region: str | None
    income_group: str | None

    class Config:
        from_attributes = True
