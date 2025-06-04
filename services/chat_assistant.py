import shutil
import zipfile
import os
import uuid

from fastapi import HTTPException, UploadFile # Keep HTTPException if used elsewhere, UploadFile is used

from db_connection.qdrant import QdrantDBManager, COLLECTION_NAME # Import COLLECTION_NAME if needed for logging or other logic
from dto.value_objects import ChunkResponse, QueryResponse
from langugae_processors.laravel_processor import LaravelProcessor
from model_interfaces.embedding_model import EmbeddingModel


class ChatAssistantService():
    """
    Service class for handling chat assistant operations.
    Service class for handling chat assistant operations.
    This will encapsulate the logic for uploading, processing,
    and querying codebases.
    """
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = QdrantDBManager()
        pass

    async def process_uploaded_zip(self, zip_file: UploadFile, description: str) -> list[str]:
        """
        Handles the end-to-end process of receiving a zip file,
        saving, extracting, and initiating processing (parsing, embedding, storage).

        Args:
            zip_file (UploadFile): The uploaded zip file.
            description (str): Description of the codebase.

        Returns:
            list[str]: A list of file paths that were extracted.

        """
        print("Started codebase Processing")
        project_path = "D:\\codes\\langGraph_venv\\code_assistant\\temp_code_uploads\\leave-management-laravel"
        # project_path =  self.save_uploaded_zip(zip_file, description)
        result = await self.process_codebase(project_path, description)
        return True

    
    

    async def process_codebase(self, project_path: str, description: str) -> list[str]:
        self.lang_processor = LaravelProcessor(project_path)
        chunks = self.lang_processor.chunk_codebase()
        embeddings =self.embedding_model.embed_chunks(chunks)
        self.vector_store.save_embeddings(embeddings, chunks)
        return chunks

                              
    def save_uploaded_zip(self, file: UploadFile, description: str) -> str:
        """
        Saves the uploaded zip file, extracts its contents.
        Returns a list of full paths to the extracted files.
        """
        #create temp folder th root level of the project
        TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_code_uploads")
        # Ensure TEMP_DIR exists (it should be created by main.py on startup)
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)
            print(f"Warning: TEMP_DIR '{TEMP_DIR}' was created by api_router.py. It should ideally be managed by main.py startup.")


        extracted_file_paths = []
        temp_zip_path = os.path.join(TEMP_DIR, file.filename)
        # Ensure extraction path is unique if multiple zips with same name are uploaded (though current logic overwrites)
        extraction_base_name = os.path.splitext(file.filename)[0]
        extraction_path = os.path.join(TEMP_DIR, extraction_base_name)

        try:
            # Save the uploaded zip file
            with open(temp_zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Create extraction directory, removing if it already exists to ensure clean extraction
            if os.path.exists(extraction_path):
                shutil.rmtree(extraction_path)
            os.makedirs(extraction_path, exist_ok=True)

            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
                # Get list of extracted files (full paths)
                for item_name in zip_ref.namelist():
                    full_item_path = os.path.join(extraction_path, item_name)
                    extracted_file_paths.append(full_item_path)

            print(f"Received description for {file.filename}: {description}")
            print(f"Extracted files for {file.filename} to: {extraction_path}")

            # Clean up the temporary zip file after extraction
            os.remove(temp_zip_path)

        except Exception as e:
            # Clean up in case of error
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
            # If extraction path was created but extraction failed or was partial, clean it up
            if os.path.exists(extraction_path) and not any(os.path.exists(p) for p in extracted_file_paths):
                shutil.rmtree(extraction_path)
            raise HTTPException(status_code=500, detail=f"Failed to process zip file '{file.filename}': {str(e)}")
        finally:
            # Ensure the file object is closed
            if hasattr(file, 'file') and file.file:
                file.file.close()

        return extraction_path
    
    def query_for_semantic_search(self, query: str, top_k: int = 3) -> QueryResponse:
        """
        Embeds the user query and searches for similar code chunks in Qdrant.

        Args:
            query (str): The user's question/query string.
            top_k (int): The number of top similar chunks to retrieve.

        Returns:
            QueryResponse: An object containing the original question, a list of
                           relevant chunk responses, and the count of found chunks.
        """
        if not query:
            # Return a QueryResponse with empty results if query is empty
            return QueryResponse(question=query, answer=[], relevant_chunks_found=0)

        print(f"Embedding query: '{query}'")
        query_embedding_list = self.embedding_model.embed_chunks([query])

        if not query_embedding_list:
            print("Could not generate embedding for the query.")
            # Return a QueryResponse with empty results if embedding fails
            return QueryResponse(question=query, answer=[], relevant_chunks_found=0)
        
        query_embedding = query_embedding_list[0]

        print(f"Searching Qdrant for top {top_k} similar chunks...")
        similar_chunks_payloads = self.vector_store.search_similar_chunks(embedding=query_embedding, limit=top_k)
        
        chunk_responses: list[ChunkResponse] = []
        if similar_chunks_payloads:
            for payload in similar_chunks_payloads:
                # Assuming payload structure from LaravelProcessor:
                # payload = {"content": "...", "metadata": {"file": "...", ...}}
                file_name = payload.get("metadata", {}).get("file", "Unknown File")
                chunk_content = payload.get("content", "No content available for this chunk.")
                
                chunk_responses.append(
                    ChunkResponse(file_name=file_name, chunk=chunk_content)
                )

        return QueryResponse(
            question=query,
            answer=chunk_responses,
            relevant_chunks_found=len(chunk_responses)
        )