
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
    # extracted_files: list[str]


class ChunkResponse(BaseModel):
    file_name: str
    chunk: str


class QueryResponse(BaseModel):
    question: str
    answer: list[ChunkResponse] # Placeholder for LLM response
    relevant_chunks_found: int # Placeholde

