from typing import List
from pydantic import BaseModel, Field

from app.Models import PropertyDto



class CommentParametersDto(BaseModel):
    body: str = Field(alias="body")
    properties: List[PropertyDto] = Field(alias="properties")
