from typing import Optional
from pydantic import BaseModel, Field


class JiraProjectSettingsDto(BaseModel):
    service_desk: Optional[bool] = Field(default=False, alias="serviceDesk")
    project_key: Optional[str] = Field(default=None, alias="projectKey")
    service_desk_id: Optional[int] = Field(default=None, alias="serviceDeskId")
    request_type_id: Optional[int] = Field(decimal=None, alias="requestTypeId")
