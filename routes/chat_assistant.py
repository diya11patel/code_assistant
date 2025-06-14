from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from pydantic import BaseModel
from utils.logger import LOGGER

from dto.value_objects import QueryRequest, QueryResponse, UploadResponse
from services.chat_assistant import ChatAssistantService # Keep for request/response models if defined here

CHAT_ASSISTANT_ROUTER = APIRouter(prefix="/chat-assistant", tags=["Chat Assistant"])
CHAT_ASSISTANT_SERVICE = ChatAssistantService()

logger = LOGGER
logger.propagate = False

@CHAT_ASSISTANT_ROUTER.post("/upload", response_model=UploadResponse)
async def upload_codebase(
    language: str,
    description: str = Form(..., description="Description of the codebase (e.g., language, structure)."),
    zip_file: UploadFile = File(..., description="A .zip file containing the codebase."),
):
    """
    Accepts a zip file containing a codebase and a description.
    It extracts the zip file, (will) process its contents, generate embeddings,
    and store them for later querying.
    """
    if not zip_file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .zip file.")
    
    logger.info(f"Received upload request for: {zip_file.filename}")
    logger.info(f"Description: {description}")

    try:
        # Process the uploaded zip file
        # For now, this helper will just save and extract.
        # Later, it will include parsing, chunking, embedding, and storing.
        extracted_files = await CHAT_ASSISTANT_SERVICE.process_uploaded_zip(zip_file, description)

        # Placeholder for actual processing
        # 1. Extract zip
        # 2. Process with relevant code processor (based on 'description' or auto-detected)
        # 3. Embed chunks
        # 4. Store embeddings

        return UploadResponse(
            message="Zip file uploaded and extracted successfully. Processing will begin.",
            filename=zip_file.filename,
            description=description,
        )
    except HTTPException as e:
        # Re-raise HTTPExceptions directly
        raise e
    except Exception as e:
        # Catch any other unexpected errors during processing
        logger.error(f"Error during upload: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@CHAT_ASSISTANT_ROUTER.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """
    Accepts a user question about the uploaded codebase.
    It (will) run embeddings on the query, retrieve relevant code chunks,
    and use an LLM to generate a response.
    """
    user_question = request.question
    logger.info(f"Received query: {user_question}")

    # Call the instance method on the CHAT_ASSISTANT_SERVICE instance
    # The query_for_semantic_search method returns a string which includes
    # the relevant chunks or a message if none are found.
    search_result = CHAT_ASSISTANT_SERVICE.query_for_semantic_search(query=user_question)

    return search_result




@CHAT_ASSISTANT_ROUTER.post("/update-code")
async def update_code_endpoint(
        request: QueryRequest,
    ): # Add return type hint
        """
        Endpoint to suggest and apply code changes based on a user query.
        This is a PoC endpoint that skips LLM query analysis and directly
        attempts to generate and apply a diff.

        Expects a JSON body with:
        {
            "query": "string"
        }

        Returns a JSON response indicating the status of the update attempt,
        the generated diff, and the results for each file.
        """
        try:
            # Call the new service method
            result = CHAT_ASSISTANT_SERVICE.suggest_and_apply_code_update(request.question)
            return result
        except Exception as e:
            # Catching broad Exception here for PoC simplicity, refine later
            logger.info(f"Error in update_code_endpoint: {e}")
            # Return a structured error response
            raise HTTPException(status_code=500, detail={"status": "error", "message": f"An unexpected error occurred during code update process: {e}"})