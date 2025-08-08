from groq import Groq
from . import config
from .tools import youtube_tools

def generate_seo_metadata(topic: str) -> dict:
    """
    Uses an LLM to generate YouTube SEO metadata based on a topic.
    """
    print("--- Generating SEO Metadata ---")
    if not config.GROQ_API_KEY:
        return {"error": "GROQ_API_KEY is not configured."}

    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = f"""
    You are a YouTube SEO expert. Your task is to generate a compelling title, a detailed description,
    and a list of relevant tags for a short, narrative video about the topic: "{topic}".

    **Instructions:**
    1.  **Title:** Create a short, hook-y, and mysterious title. It should be 60 characters or less. Do NOT use quotes around the title.
    2.  **Description:** Write a 2-3 sentence description that sets a mood and teases the story's theme without giving away the ending. Include a call to subscribe.
    3.  **Tags:** Provide a list of 10-15 relevant tags. Include a mix of broad, specific, and thematic tags. The tags should be a comma-separated list.

    **Output Format:**
    Provide the output in the following exact format, with no additional text or explanations:

    Title: [Your Generated Title]
    Description: [Your Generated Description]
    Tags: [Your Generated Tags, comma, separated]
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.7,
        )
        response_text = chat_completion.choices[0].message.content

        # Parse the response
        title = response_text.split("Title:")[1].split("Description:")[0].strip()
        description = response_text.split("Description:")[1].split("Tags:")[0].strip()
        tags_str = response_text.split("Tags:")[1].strip()
        tags = [tag.strip() for tag in tags_str.split(',')]

        metadata = {"title": title, "description": description, "tags": tags}
        print(f"Generated Title: {title}")
        print(f"Generated Description: {description}")
        print(f"Generated Tags: {tags}")

        return metadata

    except Exception as e:
        print(f"Error generating SEO metadata: {e}")
        return {"error": str(e)}


def publish_video(video_path: str, topic: str):
    """
    Orchestrates the publishing process for a video.
    """
    print("--- 🚚 Publishing Agent Initialized 🚚 ---")

    # Step 1: Generate SEO metadata
    metadata = generate_seo_metadata(topic)
    if "error" in metadata:
        print(f"Publishing failed: {metadata['error']}")
        return

    # Step 2: Upload the video to YouTube
    youtube_tools.upload_video_to_youtube(
        video_path=video_path,
        title=metadata["title"],
        description=metadata["description"],
        tags=metadata["tags"]
    )

    print("--- 🚚 Publishing Agent Finished 🚚 ---")


if __name__ == '__main__':
    # Example usage
    # NOTE: This will trigger the YouTube OAuth flow if run for the first time.
    # It also requires a dummy video file to exist.

    test_topic = "a library that contains every book never written"
    dummy_video_path = "dummy_video.mp4" # Create a dummy file for testing

    # Create a dummy file for testing if it doesn't exist
    with open(dummy_video_path, "w") as f:
        f.write("dummy")

    print(f"--- Running Publishing Test for topic: '{test_topic}' ---")
    # Ensure you have a .env file with GROQ_API_KEY and client_secrets.json
    publish_video(dummy_video_path, test_topic)
