from pydantic import BaseModel, Field
from typing import List


class FeasibilityRequest(BaseModel):
    project_description: str = Field(..., min_length=5)
    estimated_cost: str
    funding_source: str


class OperationalPartnership(BaseModel):
    pdf_files: List[str] = Field(
        ...,
        min_items=1,
        max_items=8,
        description="List of uploaded PDF file paths or URLs"
    )

    


