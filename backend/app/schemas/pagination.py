from pydantic import BaseModel, Field
from .base import CamelModel


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, extra="allow"):
    total: int
    skip: int
    limit: int
