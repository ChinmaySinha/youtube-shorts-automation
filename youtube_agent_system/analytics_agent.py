from . import knowledge_base
from .tools import youtube_tools

def analyze_video_performance(video_id: str, topic: str) -> str | None:
    """
    Gathers and analyzes performance data for a given video, then saves it.

    This function embodies the AnalyticsAgent's role. It gets stats,
    formats them into an "insight", and saves that insight to the knowledge base.

    Args:
        video_id: The ID of the YouTube video to analyze.
        topic: The original topic/title of the video.

    Returns:
        A structured string of feedback, or None if no data is found.
    """
    print(f"--- 🔎 Analytics Agent: Analyzing video '{topic}' (ID: {video_id}) ---")

    # 1. Get analytics data from the YouTube tool
    stats = youtube_tools.get_video_analytics(video_id)

    if not stats:
        print("No analytics data returned. Cannot generate insight.")
        return None

    # 2. Format the data into a structured insight string.
    # This string format is designed to be easily understood by both humans and an LLM.
    insight = (
        f"Performance insight for video with topic '{topic}': "
        f"Achieved {stats['views']} views and {stats['likes']} likes. "
        f"Average view duration was {stats['average_view_duration']} seconds."
    )
    print(f"Generated Insight: {insight}")

    # 3. Save the generated insight to the knowledge base for future use.
    # We use the video_id as the unique identifier for the document.
    knowledge_base.save_insight(
        video_id=video_id,
        insight=insight,
        metadata={
            "topic": topic,
            "views": int(stats['views']),
            "likes": int(stats['likes']),
            "avg_duration_seconds": int(stats['average_view_duration'])
        }
    )

    return insight

if __name__ == '__main__':
    # Example of how this agent would be triggered.
    # Note: This requires a REAL video ID from your channel that has analytics data.
    # Using a random one will likely return no data.
    # Replace with a real ID from your channel to test.
    test_video_id = "s600FYgI5-s" # Using the rival's video ID as a stand-in for testing
    test_topic = "My Entitled Boss Stole My Work, So I Got Pro Revenge"

    insight_result = analyze_video_performance(test_video_id, test_topic)

    if insight_result:
        print("\n--- Agent Finished ---")
        print(f"Analysis complete. Insight was generated and saved.")
    else:
        print("\n--- Agent Finished ---")
        print("Agent ran, but no analytics data was available to generate an insight.")
