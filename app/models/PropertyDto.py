from pydantic import BaseModel, Field

from app.models.ValueDto import ValueDto

class PropertyDto(BaseModel):
    key: int = Field(alias="key")
    value_pay_load: ValueDto = Field(alias="value")
