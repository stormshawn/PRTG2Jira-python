from pydantic import BaseModel, Field


class IssueDto(BaseModel):
    id: str = Field(alias="id")
    key: str = Field(alias="key")