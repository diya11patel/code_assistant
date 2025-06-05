from qdrant_client import QdrantClient

from qdrant import COLLECTION_NAME

# Connect to Qdrant
client = QdrantClient(
    host="localhost",  # or your Qdrant Cloud endpoint
    port=6333,         # default local port
    https=False        # set True if using Qdrant Cloud
)

# Name of the collection to delete
collection_name = COLLECTION_NAME

# Delete the collection
# client.delete_collection(collection_name=collection_name)
print(f"Collection '{collection_name}' deleted.")

def inspect_qdrant_collection():
    """
    Connects to Qdrant, retrieves a sample of points from the collection,
    and prints their details.
    """
    # print(f"Attempting to connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        # client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=10)
        print("Successfully connected to Qdrant.")

        print(f"\nInspecting collection: '{COLLECTION_NAME}'")

        # Check if collection exists
        try:
            collection_info = client.get_collection(collection_name=COLLECTION_NAME)
            print(f"Collection '{COLLECTION_NAME}' found.")
            print(f"  Status: {collection_info.status}")
            print(f"  Points count: {collection_info.points_count}")
            print(f"  Vectors count: {collection_info.vectors_count}") # Might differ if some points don't have vectors
            print(f"  Segments count: {collection_info.segments_count}")
            print(f"  Config: {collection_info.config}")
        except Exception as e:
            print(f"Could not get collection info for '{COLLECTION_NAME}': {e}")
            print("Please ensure the collection exists and the Qdrant server is running.")
            return

        # Retrieve a sample of points using the scroll API
        # The scroll API is suitable for iterating over all points.
        # For just a few points, client.get_points() could also be used with specific IDs.
        print("\nFetching a sample of points (up to 10 with payload):")
        
        # Using scroll to get some points with their payloads
        # You can adjust the limit
        scroll_response, next_page_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10,  # How many points to fetch
            with_payload=True,  # Include the payload
            with_vectors=True  # Set to True if you want to see the vectors too (can be very long)
        )

        if not scroll_response:
            print("No points found in the collection or failed to retrieve points.")
            return

        for i, point in enumerate(scroll_response):
            print(f"\n--- Point {i+1} ---")
            print(f"  ID: {point.id}")
            print(f"  Payload: {point.payload}")
            if point.vector: # If with_vectors=True
                 # Print only a snippet of the vector as it can be very long
                vector_snippet = str(point.vector)[:100] + "..." if len(str(point.vector)) > 100 else str(point.vector)
                print(f"  Vector (snippet): {vector_snippet}")
        
        print(f"\nFetched {len(scroll_response)} points.")
        if next_page_offset:
            print(f"There are more points in the collection. Next page offset: {next_page_offset}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    inspect_qdrant_collection()
