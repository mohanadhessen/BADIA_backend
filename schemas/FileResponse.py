from pydantic import BaseModel

class FileResponse(BaseModel):
    file_id: str
    file_key: str
    filename: str
    size: int
    content_type: str

    model_config = {"from_attributes": True}

    