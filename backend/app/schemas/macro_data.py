from pydantic import BaseModel
from uuid import UUID


class MacroDataPoint(BaseModel):
    year: int
    value: float | None
    indicator_code: str
    indicator_name: str

    class Config:
        from_attributes = True


class MacroDataResponse(BaseModel):
    country_iso3: str
    country_name: str
    data: list[MacroDataPoint]
