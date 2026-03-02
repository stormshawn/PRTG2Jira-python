from app.models import ObjectEntryDto

from typing import List
from pydantic import BaseModel, Field



class InsightDto(BaseModel):
    object_entries: List[ObjectEntryDto] = Field(alias="objectEntries",default_factory=list)