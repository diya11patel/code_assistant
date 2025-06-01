
from pydantic import BaseModel

class UploadRequest(BaseModel):
    filename: str
    description: str

class QueryRequest(BaseModel):
    question: str

class UploadResponse(BaseModel):
    message: str
    filename: str
    description: str
    extracted_files: list[str]

class QueryResponse(BaseModel):
    question: str
    answer: str # Placeholder for LLM response
    relevant_chunks_found: int # Placeholde