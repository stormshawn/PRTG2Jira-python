from pydantic import BaseModel, Field


class ServiceDeskIssue(BaseModel):
    issue_id: str = Field(..., alias="issueId")
    issue_key: str = Field(..., alias="issueKey")
    request_type_id: str = Field(..., alias="requestTypeId")
    service_desk_id: str = Field(..., alias="serviceDeskId")
