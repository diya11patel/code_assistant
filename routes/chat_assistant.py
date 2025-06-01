from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from pydantic import BaseModel

from dto.value_objects import QueryRequest, QueryResponse, UploadResponse # Keep for request/response models if defined here

CHAT_ASSISTANT_ROUTER = APIRouter(prefix="/chat-assistant", tags=["Chat Assistant"])

@CHAT_ASSISTANT_ROUTER.post("/upload", response_model=UploadResponse)
async def upload_codebase(
    description: str = Form(..., description="Description of the codebase (e.g., language, structure)."),
    zip_file: UploadFile = File(..., description="A .zip file containing the codebase.")
):
    """
    Accepts a zip file containing a codebase and a description.
    It extracts the zip file, (will) process its contents, generate embeddings,
    and store them for later querying.
    """
    if not zip_file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .zip file.")
    
    print(f"Received upload request for: {zip_file.filename}")
    print(f"Description: {description}")

    try:
        # Process the uploaded zip file
        # For now, this helper will just save and extract.
        # Later, it will include parsing, chunking, embedding, and storing.
        extracted_files = process_uploaded_zip(zip_file, description)

        # Placeholder for actual processing
        # 1. Extract zip
        # 2. Process with relevant code processor (based on 'description' or auto-detected)
        # 3. Embed chunks
        # 4. Store embeddings

        return UploadResponse(
            message="Zip file uploaded and extracted successfully. Processing will begin.",
            filename=zip_file.filename,
            description=description,
            extracted_files=[os.path.basename(f) for f in extracted_files if os.path.isfile(f)] # Show only file names
        )
    except HTTPException as e:
        # Re-raise HTTPExceptions directly
        raise e
    except Exception as e:
        # Catch any other unexpected errors during processing
        print(f"Error during upload: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@CHAT_ASSISTANT_ROUTER.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """
    Accepts a user question about the uploaded codebase.
    It (will) run embeddings on the query, retrieve relevant code chunks,
    and use an LLM to generate a response.
    """
    user_question = request.question
    print(f"Received query: {user_question}")

    # Placeholder for actual query processing
    # 1. Run embedding on the query (user_question)
    # 2. Retrieve top N code chunks from the vector store
    # 3. Format context and query for LLM
    # 4. Run with LLM
    # 5. Return LLM response

    # Dummy response for now
    dummy_answer = f"This is a placeholder answer for your question: '{user_question}'. LLM integration is pending."
    relevant_chunks_found = 0 # Placeholder

    return QueryResponse(
        question=user_question,
        answer=dummy_answer,
        relevant_chunks_found=relevant_chunks_found
    )
