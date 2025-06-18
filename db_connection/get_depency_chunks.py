from qdrant_client import QdrantClient, models
from utils.logger import LOGGER

from qdrant import COLLECTION_NAME

# Connect to Qdrant
client = QdrantClient(
    host="localhost",  # or your Qdrant Cloud endpoint
    port=6333,         # default local port
    https=False        # set True if using Qdrant Cloud
)

# # Name of the collection to delete (Uncomment to use the delete functionality)
# collection_name_to_delete = COLLECTION_NAME

# # Delete the collection (Uncomment to use the delete functionality)
# client.delete_collection(collection_name=collection_name_to_delete)
# logger.info(f"Collection '{collection_name_to_delete}' deleted.")

def inspect_qdrant_collection():
    """
    Connects to Qdrant, retrieves a sample of points from the collection,
    and logger.infos their details.
    """
    # logger.info(f"Attempting to connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        # client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=10)
        LOGGER.info("Successfully connected to Qdrant.")

        LOGGER.info(f"\nInspecting collection: '{COLLECTION_NAME}'")

        # Check if collection exists
        try:
            collection_info = client.get_collection(collection_name=COLLECTION_NAME)
            LOGGER.info(f"Collection '{COLLECTION_NAME}' found.")
            LOGGER.info(f"  Status: {collection_info.status}")
            LOGGER.info(f"  Points count: {collection_info.points_count}")
            LOGGER.info(f"  Vectors count: {collection_info.vectors_count}") # Might differ if some points don't have vectors
            LOGGER.info(f"  Segments count: {collection_info.segments_count}")
            LOGGER.info(f"  Config: {collection_info.config}")
        except Exception as e:
            LOGGER.info(f"Could not get collection info for '{COLLECTION_NAME}': {e}")
            LOGGER.info("Please ensure the collection exists and the Qdrant server is running.")
            return

        # Retrieve a sample of points using the scroll API
        # The scroll API is suitable for iterating over all points.
        # For just a few points, client.get_points() could also be used with specific IDs.
        LOGGER.info("\nFetching a sample of points (up to 10 with payload):")
        LOGGER.info("Filtering for chunks with non-empty 'dependencies' list.")

        # Define the filter for non-empty 'dependencies' list
        # This filter checks if the 'dependencies' array field has a count (cardinality) >= 1
        non_empty_dependencies_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="dependencies",  # Path to the field in the payload
                    range=models.Range(gte=1)  # Check if the array length is greater than or equal to 1
                )
            ]
        )

        # Using scroll to get some points with their payloads
        scroll_response, next_page_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10,  # How many points to fetch
            with_payload=True,  # Include the payload
            with_vectors=False, # Set to True if you want to see the vectors too (can be very long)
            scroll_filter=non_empty_dependencies_filter # Apply the filter
        )

        if not scroll_response:
            LOGGER.info("No points found in the collection or failed to retrieve points.")
            return

        for i, point in enumerate(scroll_response):
            LOGGER.info(f"\n--- Point {i+1} ---")
            LOGGER.info(f"  ID: {point.id}")
            LOGGER.info(f"  Payload: {point.payload}")
            if point.vector: # If with_vectors=True
                 # logger.info only a snippet of the vector as it can be very long
                vector_snippet = str(point.vector)[:100] + "..." if len(str(point.vector)) > 100 else str(point.vector)
                LOGGER.info(f"  Vector (snippet): {vector_snippet}")
        
        LOGGER.info(f"\nFetched {len(scroll_response)} points.")
        if next_page_offset:
            LOGGER.info(f"There are more points in the collection. Next page offset: {next_page_offset}")

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")

if __name__ == "__main__":
    inspect_qdrant_collection()