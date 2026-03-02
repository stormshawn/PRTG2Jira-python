from pydantic import BaseModel, Field

class ObjectEntryDto(BaseModel):
    id: int = Field(alias="id")
    label: str = Field(alias="label")
    object_key: str = Field(alias="objectKey")
