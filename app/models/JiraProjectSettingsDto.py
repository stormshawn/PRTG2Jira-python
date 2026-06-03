from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class JiraProjectSettingsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    service_desk: Optional[bool] = Field(default=False, alias="serviceDesk")
    project_key: Optional[str] = Field(default="", alias="projectKey")
    service_desk_id: Optional[int] = Field(default=None, alias="serviceDeskId")
    request_type_id: Optional[int] = Field(default=None, alias="requestTypeId")
