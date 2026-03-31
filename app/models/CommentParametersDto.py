from typing import List
from pydantic import BaseModel, Field

from app.models.PropertyDto import PropertyDto


class CommentParametersDto(BaseModel):
    body: str = Field(alias="body")
    properties: List[PropertyDto] = Field(default_factory=list, alias="properties")
