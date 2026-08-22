from typing import Optional
from pydantic import BaseModel


class RootHealthResponse(BaseModel):
    status: str = "ok"
    service: str = "modelvault"


class DetailedHealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
