from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


ConnectorStatus = Literal["live", "planned", "user_upload", "deprecated"]
LicenseCategory = Literal["A", "B", "C", "D"]


class DataSourceRead(BaseModel):
    id: UUID
    source_id: str
    source_name: str
    source_type: str
    access_method: str
    license_category: LicenseCategory
    update_frequency: str
    requires_approval: bool
    redistribution_allowed: bool
    citation_required: bool
    data_owner: str
    connector_status: ConnectorStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DataSourceList(BaseModel):
    total: int
    items: list[DataSourceRead]
