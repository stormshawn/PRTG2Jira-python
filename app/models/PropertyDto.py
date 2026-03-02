from pydantic import BaseModel, Field

from app.models import ValueDto

class PropertyDto(BaseModel):
    key: int = Field(alias="key")
    value_pay_load: ValueDto = Field(alias="value")
