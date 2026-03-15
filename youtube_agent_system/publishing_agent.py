from .tools.llm_client import chat_completion, SEO_PARAMS
import random
from . import config
from .tools import youtube_tools

def generate_seo_metadata(topic: str, content_category: str = "AITA") -> dict:
    """
    Uses an LLM to generate YouTube Shorts SEO metadata optimized for the
    Shorts algorithm (categorization via title, description, hashtags, and spoken words).
    
    Algorithm insights applied:
    - #shorts hashtag is mandatory for algorithm recognition
    - Category-specific hashtags help algorithm match to right audience
    - Description keywords reinforce content categorization
    - Title must be hook-y and under 60 chars for mobile display
    - Engagement CTA drives comments/shares (algorithm ranking signal)
    - Cross-platform tags boost multi-platform discovery
    """
    print("--- Generating Shorts-Optimized SEO Metadata ---")

    # Get category-specific hashtags
    category_tags = config.SHORTS_CATEGORY_HASHTAGS.get(
        content_category, config.SHORTS_CATEGORY_HASHTAGS.get("STORIES", [])
    )
    default_tags = config.SHORTS_DEFAULT_HASHTAGS
    
    # Add cross-platform tags if enabled
    cross_tags = config.SHORTS_CROSS_PLATFORM_TAGS if config.SHORTS_CROSS_PLATFORM_ENABLED else []
    
    # Combine and deduplicate
    all_hashtags = list(dict.fromkeys(default_tags + category_tags + cross_tags))
    hashtag_str = " ".join(all_hashtags[:10])  # Max 10 hashtags

    # Select a random engagement CTA for this video
    engagement_cta = random.choice(config.SHORTS_ENGAGEMENT_CTA_TEMPLATES)

    prompt = f"""
    You are a YouTube Shorts SEO expert who understands the Shorts algorithm.
    Generate optimized metadata for a Short about: "{topic}"
    Content category: {content_category}

    **ALGORITHM RULES TO FOLLOW:**
    1. The Shorts algorithm uses title + description + spoken words to categorize content
    2. Titles must be under 60 characters, shocking/hook-y for mobile feeds
    3. Description must include relevant keywords AND hashtags for discovery
    4. Tags should mix broad discovery terms with niche-specific terms
    5. Viewer interaction (comments, shares) is a ranking signal — include a question/CTA

    **Instructions:**
    1.  **Title:** Create a short, mysterious, hook-y title. MAX 60 characters. Must make someone STOP scrolling. Do NOT use quotes.
    2.  **Description:** Write 2-3 punchy sentences that tease the story without spoilers. Then add this engagement line: "{engagement_cta}" Then add: "Like and follow for more!" Finally add this hashtag line: {hashtag_str}
    3.  **Tags:** Provide 10-15 tags. Include: the story category ({content_category.lower()}), "reddit stories", "shorts", "storytime", plus topic-specific tags. Comma-separated.

    **Output Format (exact, no extra text):**

    Title: [Your Title]
    Description: [Your Description]
    Tags: [tag1, tag2, tag3, ...]
    """

    try:
        response_text = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            params=SEO_PARAMS,
            task="seo_metadata"
        )
        if not response_text:
            return {"error": "All LLM providers failed"}

        # Parse the response
        title = response_text.split("Title:")[1].split("Description:")[0].strip()
        description = response_text.split("Description:")[1].split("Tags:")[0].strip()
        tags_str = response_text.split("Tags:")[1].strip()
        tags = [tag.strip() for tag in tags_str.split(',')]

        # Ensure engagement CTA is in description if LLM missed it
        if "?" not in description and "!" not in description:
            description += f"\n\n{engagement_cta}"

        # Ensure hashtags are in description if LLM missed them
        if "#shorts" not in description.lower():
            description += f"\n\n{hashtag_str}"

        # Ensure #Shorts tag is always present
        if "#Shorts" not in tags and "#shorts" not in tags:
            tags.insert(0, "#Shorts")

        metadata = {"title": title, "description": description, "tags": tags}
        print(f"Generated Title: {title}")
        print(f"Generated Description: {description[:100]}...")
        print(f"Generated Tags: {tags[:5]}... ({len(tags)} total)")
        print(f"Engagement CTA: {engagement_cta}")

        return metadata

    except Exception as e:
        print(f"Error generating SEO metadata: {e}")
        return {"error": str(e)}


def publish_video(video_path: str, topic: str, content_category: str = "AITA") -> str | None:
    """
    Orchestrates the publishing process for a video and returns the new video ID.
    Passes content_category to SEO metadata for Shorts algorithm optimization.
    """
    print("--- Publishing Agent Initialized ---")

    # Step 1: Generate Shorts-optimized SEO metadata
    metadata = generate_seo_metadata(topic, content_category=content_category)
    if "error" in metadata:
        print(f"Publishing failed: {metadata['error']}")
        return None

    # Step 2: Upload the video to YouTube and get the ID back
    video_id = youtube_tools.upload_video_to_youtube(
        video_path=video_path,
        title=metadata["title"],
        description=metadata["description"],
        tags=metadata["tags"]
    )

    print("--- Publishing Agent Finished ---")
    return video_id # <-- Return the real video ID


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

def update_video_metadata(video_id: str, new_title: str, new_description: str):
    """
    (Placeholder for A/B Testing) Updates the metadata of an existing video.

    This function demonstrates how you could implement A/B testing. For example,
    you could call this after 24 hours to change the title and see if it
    improves click-through rate.
    """
    print(f"--- (A/B Testing Groundwork) Updating metadata for video {video_id} ---")

    try:
        youtube = youtube_tools.get_youtube_service()
        if not youtube:
            print("Could not get YouTube service. Aborting update.")
            return

        # First, get the existing video snippet to preserve other fields
        request = youtube.videos().list(part="snippet,status", id=video_id)
        response = request.execute()

        if not response.get("items"):
            print(f"Video with ID {video_id} not found.")
            return

        video_data = response["items"][0]
        video_data["snippet"]["title"] = new_title
        video_data["snippet"]["description"] = new_description

        update_request = youtube.videos().update(
            part="snippet",
            body=video_data
        )
        update_request.execute()
        print(f"Successfully updated video {video_id} with new title: '{new_title}'")

    except Exception as e:
        print(f"An error occurred during video metadata update: {e}")