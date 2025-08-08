# --- Phase 3: The Intelligence Layer ---
# This file will manage the system's long-term memory using a vector database.

# The recommended free and open-source choice is ChromaDB.
# To use this, you would run: pip install chromadb

# The Knowledge Base stores insights from the AnalyticsAgent and provides them
# to the StrategyAgent, enabling the system to learn over time.

import chromadb
import os
from . import config

# Initialize ChromaDB client. It can be persistent or in-memory.
# For persistence, provide a path.
persistent_client = chromadb.PersistentClient(path=os.path.join(config.ASSETS_DIR, "chroma_db"))

# Get or create a collection. Collections are like tables in a SQL database.
collection = persistent_client.get_or_create_collection(
    name="youtube_insights"
)

def save_insight(video_id: str, insight: str):
    """
    Saves a performance insight into the vector database.

    Args:
        video_id: The ID of the video the insight is about.
        insight: The text of the insight.
    """
    print(f"--- Knowledge Base: Saving insight for video {video_id} ---")

    # In ChromaDB, each entry needs a unique ID. We'll use the video_id.
    # The 'documents' are the text snippets we want to store and search.
    try:
        collection.add(
            documents=[insight],
            ids=[video_id]
            # Metadatas can also be added here for filtering, e.g.,
            # metadatas=[{"topic": "space", "ctr": 0.05}]
        )
        print("Insight saved successfully.")
    except Exception as e:
        # ChromaDB can throw an error if the ID already exists.
        # In a real system, you might want to use `upsert` instead of `add`.
        print(f"Could not save insight. It might already exist. Error: {e}")


def query_insights(query: str, n_results: int = 3) -> list[str]:
    """
    Queries the knowledge base for relevant insights.

    Args:
        query: The search query (e.g., "high click-through rates").
        n_results: The number of results to return.

    Returns:
        A list of the most relevant insights.
    """
    print(f"--- Knowledge Base: Querying for '{query}' ---")
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results['documents'][0] if results['documents'] else []

if __name__ == '__main__':
    # Example of how the knowledge base would be used.

    # 1. AnalyticsAgent saves insights after analyzing videos.
    save_insight("video_id_1", "Topic 'space exploration' resulted in high average view duration.")
    save_insight("video_id_2", "Mysterious titles like 'The Last Secret' led to a high click-through rate.")
    save_insight("video_id_3", "Videos under 60 seconds had better audience retention.")

    # 2. StrategyAgent queries for insights to decide on a new video.
    print("\n--- Strategy Query 1 ---")
    relevant_insights = query_insights("What makes a good title?")
    print("Relevant Insights:", relevant_insights)

    print("\n--- Strategy Query 2 ---")
    relevant_insights = query_insights("ideas for long videos")
    print("Relevant Insights:", relevant_insights)
