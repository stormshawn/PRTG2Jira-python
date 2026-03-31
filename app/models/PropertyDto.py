from pydantic import BaseModel, Field

from app.models.ValueDto import ValueDto


class PropertyDto(BaseModel):
    key: str = Field(alias="key")
    value_payload: ValueDto = Field(default_factory=ValueDto, alias="value")
