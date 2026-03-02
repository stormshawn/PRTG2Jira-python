from pydantic import BaseModel


class ProblemResponseDto(BaseModel):
    detail: str
    status_code: int 