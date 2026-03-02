from pydantic import BaseModel, Field

class ValueDto(BaseModel):
    internal: bool = True # no need for field as name (internal) is the same as Jsonpropteryname
