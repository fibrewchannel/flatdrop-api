from pydantic import BaseModel

class UploadPayload(BaseModel):
    filename: str
    content: str

class ValidationPayload(BaseModel):
    filename: str
    content: str
    
class TesseractCoordinates(BaseModel):
    x_structure: str
    y_transmission: str
    z_purpose: str
    w_terrain: str
    tesseract_key: str

class TagAuditResponse(BaseModel):
    total_tags: int
    total_instances: int
    top_50_tags: list
    unique_tags: list

class ReorganizationSuggestion(BaseModel):
    action: str
    priority: str
    total_files: int
    suggested_target_path: str
