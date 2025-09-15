from pydantic import BaseModel

class UploadPayload(BaseModel):
    filename: str
    content: str

class ValidationPayload(BaseModel):
    filename: str
    content: str
