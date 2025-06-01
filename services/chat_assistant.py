import shutil
import zipfile
import os
import uuid

from fastapi import HTTPException, UploadFile

from db_connection.qdrant import QdrantDBManager
from langugae_processors.laravel_processor import LaravelProcessor
from model_interfaces.embedding_model import EmbeddingModel

TEMP_DIR = "/tmp/code_uploads"

class ChatAssistantService():
    """
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
        
        project_path =  self.save_uploaded_zip(zip_file, description)
        result = self.process_codebase(project_path, description)

    
    

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
        # Ensure TEMP_DIR exists (it should be created by main.py on startup)
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)
            print(f"Warning: TEMP_DIR '{TEMP_DIR}' was created by api_router.py. It should ideally be managed by main.py startup.")


        extracted_file_paths = []
        temp_zip_path = os.path.join(TEMP_DIR, file.f=ilename)
        # Ensure extraction path is unique if multiple zips with same name are uploaded (though current logic overwrites)
        extraction_base_name = os.path.splitext(file.filename)[0]
        extraction_path = os.path.join(TEMP_DIR, extraction_base_name)

        try:
            # # Save the uploaded zip file
            # with open(temp_zip_path, "wb") as buffer:
            #     shutil.copyfileobj(file.file, buffer)

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