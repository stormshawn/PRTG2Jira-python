from typing import Optional
from pydantic import BaseModel, Field


class JiraProjectSettingsDto(BaseModel):
    service_desk: bool = Field(alias="serviceDesk")
    project_key: str = Field(alias="projectKey")
    service_desk_id: Optional[int] = Field(alias="serviceDeskId")
    request_type_id: Optional[int] = Field(alias="requestTypeId")