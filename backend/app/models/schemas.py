from pydantic import BaseModel, Field
from typing import Optional, Literal


class JobCreate(BaseModel):
    input_name: str = Field(..., min_length=1)
    logo_name: str = Field(..., min_length=1)
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right", "full"] = "bottom-right"
    scale: float = 0.2


class JobStatus(BaseModel):
    id: str
    status: str
    input_name: str
    logo_name: str
    output_name: Optional[str] = None
    position: str = "bottom-right"
    scale: float = 0.2
    progress: int = 0  # 0-100 percentage
