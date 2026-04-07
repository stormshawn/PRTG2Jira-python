from typing import Optional

from pydantic import BaseModel


class JiraRequestDto(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None
    sensor_id: int
    priority: Optional[str] = None
    probe: Optional[str] = None
    device: Optional[str] = None
    message: Optional[str] = None
    tags: Optional[str] = None
