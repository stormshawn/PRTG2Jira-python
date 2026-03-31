from pydantic import BaseModel, Field


class ValueDto(BaseModel):
    internal: bool = Field(True, alias="internal")
