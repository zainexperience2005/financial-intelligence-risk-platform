from pydantic import BaseModel


class APIError(BaseModel):
    error: str
    message: str
    request_id: str | None = None
