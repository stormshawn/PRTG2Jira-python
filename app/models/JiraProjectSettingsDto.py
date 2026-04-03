from typing import Optional
from pydantic import BaseModel, Field


class JiraProjectSettingsDto(BaseModel):
    service_desk: bool = Field(False, alias="serviceDesk")
    project_key: str = Field("", alias="projectKey")
    service_desk_id: Optional[int] = Field(None, alias="serviceDeskId")
    request_type_id: Optional[int] = Field(None, alias="requestTypeId")
