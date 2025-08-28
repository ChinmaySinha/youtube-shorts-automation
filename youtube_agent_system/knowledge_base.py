import os
import chromadb
from . import config

# Initialize a persistent ChromaDB client.
# This stores the database on disk in the specified path.
persistent_client = chromadb.PersistentClient(
    path=os.path.join(config.ASSETS_DIR, "chroma_db")
)

# Get or create a collection. Collections are like tables in a SQL database.
# Using a constant name for the collection.
INSIGHTS_COLLECTION_NAME = "youtube_insights_v1"
collection = persistent_client.get_or_create_collection(
    name=INSIGHTS_COLLECTION_NAME
)

def save_insight(video_id: str, insight: str, metadata: dict):
    """
    Saves or updates a performance insight in the vector database.

    Args:
        video_id: The unique ID of the video (used as the document ID).
        insight: The text of the insight (e.g., "Video '...' got X views...").
        metadata: A dictionary of structured data (views, likes, etc.).
    """
    print(f"--- 🧠 Knowledge Base: Saving insight for video {video_id} ---")

    # ChromaDB's `upsert` is perfect here: it adds the document if it's new,
    # or updates it if the ID already exists. This prevents errors on re-analysis.
    try:
        collection.upsert(
            ids=[video_id],
            documents=[insight],
            metadatas=[metadata]
        )
        print("Insight saved successfully.")
    except Exception as e:
        print(f"Error saving insight to ChromaDB: {e}")

def query_insights(query: str, n_results: int = 3) -> list[str]:
    """
    Queries the knowledge base for insights most relevant to a text query.

    Args:
        query: The search query (e.g., "high click-through rate topics").
        n_results: The number of results to return.

    Returns:
        A list of the most relevant insight documents (strings).
    """
    print(f"--- 🧠 Knowledge Base: Querying for '{query}' with {n_results} results ---")
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] if results.get('documents') else []
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []

def get_all_insights() -> list[str]:
    """
    Retrieves all insights currently stored in the knowledge base.

    Returns:
        A list of all insight documents.
    """
    print("--- 🧠 Knowledge Base: Retrieving all insights ---")
    try:
        # The `get()` method without IDs retrieves all entries.
        # We include metadatas to potentially use them later.
        all_items = collection.get(include=["documents"])
        return all_items['documents'] if all_items else []
    except Exception as e:
        print(f"Error getting all insights from ChromaDB: {e}")
        return []


if __name__ == '__main__':
    # Example of how the knowledge base would be used.
    print("--- Testing Knowledge Base ---")

    # 1. AnalyticsAgent saves insights
    test_metadata_1 = {"topic": "AITA for exposing my ex", "views": 15000, "likes": 1200}
    save_insight("video_id_1", f"Insight for video 1: {test_metadata_1}", test_metadata_1)

    test_metadata_2 = {"topic": "Pro revenge on my boss", "views": 50000, "likes": 4500}
    save_insight("video_id_2", f"Insight for video 2: {test_metadata_2}", test_metadata_2)

    # 2. StrategyAgent queries for insights
    print("\n--- Strategy Query ---")
    relevant_insights = query_insights("stories about revenge", n_results=1)
    print("Most relevant insight:", relevant_insights)

    # 3. StrategyAgent gets all data to synthesize
    print("\n--- Strategy Get All ---")
    all_insights = get_all_insights()
    print(f"Retrieved {len(all_insights)} total insights.")
    print("All stored insights:", all_insights)
