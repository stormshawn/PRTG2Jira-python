from typing import List
from pydantic import BaseModel, Field
from app.models import IssueDto

class JiraIssuesDto(BaseModel):
    total: int = Field(alias="total")
    issues: List[IssueDto] = Field(alias="issues",default_factory=list)