from pydantic import BaseModel

class JiraRequestDto(BaseModel):
    status: str
    name: str
    sensor_id: int
    priority: str
    probe: str
    device: str
    message: str
    tags: str


