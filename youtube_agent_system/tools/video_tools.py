import os
import requests
import random
from .. import config

def _get_pexels_video() -> str | None:
    """Helper function to fetch a video from the Pexels API."""
    if not config.PEXELS_API_KEY:
        print("Warning: PEXELS_API_KEY is not configured. Cannot fetch from Pexels.")
        return None

    gameplay_query = random.choice(config.GAMEPLAY_QUERIES)
    print(f"--- Searching for background video on Pexels with query: '{gameplay_query}' ---")

    headers = {"Authorization": config.PEXELS_API_KEY}
    query_params = {
        "query": gameplay_query,
        "orientation": "portrait",
        "per_page": 15,
        "size": "medium"
    }

    try:
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=query_params)
        response.raise_for_status()
        data = response.json()

        if not data.get("videos"):
            print(f"No videos found for query: '{gameplay_query}' on Pexels.")
            return None

        video_info = data["videos"][0]

        # **BUG FIX:** Add safety check for 'video_files' key
        video_files = video_info.get('video_files')
        if not video_files:
            print(f"Warning: Video found (ID: {video_info.get('id')}) but it contains no video files. Skipping.")
            return None

        video_link = next((f['link'] for f in video_files if 'hd' in f.get('quality', '')), video_files[0]['link'])

        print(f"Found video: {video_info.get('url')}")
        print(f"Downloading from: {video_link}")

        video_response = requests.get(video_link, stream=True)
        video_response.raise_for_status()

        video_filename = f"background_{gameplay_query.replace(' ', '_')}.mp4"
        video_path = os.path.join(config.ASSETS_DIR, video_filename)

        with open(video_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Video downloaded successfully to: {video_path}")
        return video_path

    except requests.exceptions.RequestException as e:
        print(f"Error fetching video from Pexels: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Pexels fetch: {e}")
        return None

def get_background_video() -> str | None:
    """
    Finds and downloads a background video, with a local fallback system.

    1. Tries to fetch a random gameplay video from Pexels.
    2. If that fails, it checks for a local fallback path in the config.
    3. If a valid local file is found, it uses that.
    4. If all else fails, it returns None.
    """
    # Step 1: Try to get video from Pexels
    video_path = _get_pexels_video()

    if video_path:
        return video_path

    # Step 2: If Pexels fails, try the local fallback
    print("--- Pexels search failed. Attempting to use local fallback video. ---")
    fallback_path = config.LOCAL_VIDEO_FALLBACK_PATH

    if fallback_path and os.path.exists(fallback_path):
        print(f"Found valid local fallback video at: {fallback_path}")
        return fallback_path
    elif fallback_path:
        print(f"Warning: Local fallback path is set, but file not found at: {fallback_path}")
        return None
    else:
        print("No local fallback path set. Production cannot continue.")
        return None

if __name__ == '__main__':
    # Example usage
    video_file = get_background_video()
    if video_file:
        print(f"\nSuccessfully retrieved background video: {video_file}")
    else:
        print("\nFailed to retrieve any background video.")
