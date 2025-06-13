# qdrant_manager.py
import os
import uuid
from typing import Any, List
from typing_extensions import Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333)) # Ensure port is an integer
COLLECTION_NAME = "codebase_chunks_v2" # Suitable collection name
# BGE-M3 embedding dimension
EMBEDDING_DIMENSION = 1536
DISTANCE_METRIC = models.Distance.COSINE


class QdrantDBManager:
    """
    Manages the connection to Qdrant and ensures the necessary collection exists.
    """
    client: QdrantClient

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        """
        Initializes the Qdrant client and ensures the collection is ready.

        Args:
            host (str): The host address of the Qdrant instance.
            port (int): The port number of the Qdrant instance.
        """
        print(f"Attempting to connect to Qdrant at {host}:{port}...")
        try:
            self.client = QdrantClient(host=host, port=port, timeout=20)
            print("Successfully connected to Qdrant.")
            self._ensure_collection_exists()
            # for using qdrant cloud
            # self.client = QdrantClient(
            #     url="https://3aa59a3e-1522-4fde-a5e7-6e43b1780b01.eu-west-1-0.aws.cloud.qdrant.io",
            #     api_key=QDRANT_API_KEY,
            #     timeout=60.0
            # )
        except Exception as e:
            print(f"An unexpected error occurred during Qdrant client initialization: {e}")
            raise

    def _ensure_collection_exists(self):
        """
        Checks if the specified collection exists, and creates it if it doesn't.
        """
        try:
            self.client.get_collection(collection_name=COLLECTION_NAME)
            print(f"Collection '{COLLECTION_NAME}' already exists.")
        except UnexpectedResponse as e:
            # Qdrant client raises UnexpectedResponse with status code 404 if collection not found
            if e.status_code == 404:
                print(f"Collection '{COLLECTION_NAME}' not found. Creating it now...")
                try:
                    self.client.create_collection(
                        collection_name=COLLECTION_NAME,
                        vectors_config=models.VectorParams(
                            size=EMBEDDING_DIMENSION,
                            distance=DISTANCE_METRIC
                        )
                    ) 
                    print(f"Collection '{COLLECTION_NAME}' created successfully with vector size {EMBEDDING_DIMENSION} and {DISTANCE_METRIC} distance.")
                except Exception as create_exc:
                    print(f" Failed to create collection '{COLLECTION_NAME}': {create_exc}")
                    raise
            else:
                # Some other unexpected error occurred
                print(f" Error checking collection '{COLLECTION_NAME}': {e}")
                raise
        except Exception as e:
            print(f"An unexpected error occurred while checking collection '{COLLECTION_NAME}': {e}")
            raise

    def get_client(self) -> QdrantClient:
        """
        Returns the active Qdrant client instance.

        Returns:
            QdrantClient: The initialized Qdrant client.
        """
        return self.client

    def save_embeddings(
            self, 
            embeddings: List[List[float]], 
            payloads: List[Dict[str, Any]],
        ) -> bool:
            """
            Saves embeddings and their corresponding payloads to the Qdrant collection.

            Args:
                embeddings (List[List[float]]): A list of embedding vectors.
                payloads (List[Dict[str, Any]]): A list of metadata dictionaries,
                                                one for each embedding.
            Returns:
                bool: True if the operation was successful, False otherwise.
            """
            if not embeddings:
                print("No embeddings provided to save.")
                return False
            
            if len(embeddings) != len(payloads):
                print("Error: The number of embeddings and payloads must be the same.")
                return False


            point_ids = [uuid.uuid4().hex for _ in embeddings]

            points_to_upsert = [
                models.PointStruct(
                    id=point_ids[i],
                    vector=embedding,
                    payload=payload
                )
                for i, (embedding, payload) in enumerate(zip(embeddings, payloads))
            ]

            try:
                print(f"Attempting to save {len(points_to_upsert)} points to collection '{COLLECTION_NAME}'...")
                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points_to_upsert,
                    wait=True  # Wait for the operation to complete
                )
                print(f"Successfully saved {len(points_to_upsert)} points to '{COLLECTION_NAME}'.")
                return True
            except UnexpectedResponse as e:
                print(f"Qdrant API error during upsert: {e.status_code} - {e.content.decode() if e.content else 'No content'}")
                return False
            except Exception as e:
                print(f"An unexpected error occurred while saving embeddings: {e}")
                return False

    def search_similar_chunks(
        self,
        embedding: List[float],
        limit: int = 5,
        score_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Searches for chunks in Qdrant that are semantically similar to the given embedding.

        Args:
            embedding (List[float]): The embedding vector of the query.
            limit (int): The maximum number of similar chunks to retrieve.
            score_threshold (float, optional): Minimum similarity score for a chunk to be returned.
                                              Depends on the distance metric (e.g., for COSINE, higher is better).

        Returns:
            List[Dict[str, Any]]: A list of payloads from the most similar chunks.
        """
        if not embedding:
            print("No embedding provided for search.")
            return []
        try:
            print(f"Searching in collection '{COLLECTION_NAME}' with limit {limit}...")
            search_results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold # Only include results above this score
            )
            print(f"Found {len(search_results)} similar chunks.")
            return [hit.payload for hit in search_results if hit.payload is not None]
        except Exception as e:
            print(f"An error occurred during Qdrant search: {e}")
            return []
