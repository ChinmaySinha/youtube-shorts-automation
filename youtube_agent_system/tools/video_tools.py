import os
import requests
import random
from .. import config

def get_background_video() -> str | None:
    """
    Finds and downloads a suitable background gameplay video from Pexels.

    This function now ignores the story topic and randomly selects a gameplay
    query from the list in config.py to ensure a consistent visual style.

    Returns:
        The file path of the downloaded video, or None if an error occurs.
    """
    if not config.PEXELS_API_KEY:
        print("Error: PEXELS_API_KEY is not configured in the .env file.")
        return None

    # Randomly select a gameplay query
    gameplay_query = random.choice(config.GAMEPLAY_QUERIES)
    print(f"--- Searching for background video on Pexels with query: '{gameplay_query}' ---")

    headers = {
        "Authorization": config.PEXELS_API_KEY
    }

    # Search for vertically oriented videos to match the 9:16 short format
    query_params = {
        "query": gameplay_query,
        "orientation": "portrait",
        "per_page": 15, # Search more results to find a longer video
        "size": "medium" # small, medium, large
    }

    try:
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=query_params)
        response.raise_for_status()

        data = response.json()

        if not data["videos"]:
            print(f"No vertical videos found for topic: {topic}. Trying any orientation.")
            query_params.pop("orientation")
            response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=query_params)
            response.raise_for_status()
            data = response.json()
            if not data["videos"]:
                print(f"No videos found for topic: {topic} on Pexels.")
                return None

        # Select the first video found
        video_info = data["videos"][0]

        # Find the best quality link for download (preferring higher resolution)
        video_link = ""
        for file in video_info['video_files']:
            if 'hd' in file['quality']: # Prioritize HD quality
                video_link = file['link']
                break
        if not video_link: # Fallback to the first available link
            video_link = video_info['video_files'][0]['link']

        print(f"Found video: {video_info['url']}")
        print(f"Downloading from: {video_link}")

        # Download the video
        video_response = requests.get(video_link, stream=True)
        video_response.raise_for_status()

        # Save the video
        video_filename = f"background_{topic.replace(' ', '_')}.mp4"
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
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    test_topic = "ocean waves"
    video_file = get_background_video(test_topic)
    if video_file:
        print(f"\nDownloaded video path: {video_file}")
    else:
        print("\nFailed to download video.")
