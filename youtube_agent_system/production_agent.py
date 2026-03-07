# youtube_agent_system/production_agent.py
import os
import requests
from .tools import audio_tools, video_tools, editing_tools
from . import config


def _get_background_video() -> str | None:
    """
    Get a background video path. Tries local files first,
    downloads from Pexels if none found (for cloud/GitHub Actions).
    """
    # Check for any .mp4 in the project directory
    base_dir = config.BASE_DIR
    for f in os.listdir(base_dir):
        if f.endswith('.mp4') and 'generated' not in f.lower():
            path = os.path.join(base_dir, f)
            print(f"  Using local background video: {f}")
            return path
    
    # No local video found — download from Pexels
    print("  No local background video found. Downloading from Pexels...")
    pexels_key = os.getenv('PEXELS_API_KEY', config.PEXELS_API_KEY if hasattr(config, 'PEXELS_API_KEY') else '')
    
    if not pexels_key:
        print("  ERROR: No Pexels API key. Cannot download background video.")
        return None
    
    try:
        # Search for satisfying/gameplay videos (vertical, HD)
        headers = {"Authorization": pexels_key}
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": "satisfying abstract", "orientation": "portrait", "size": "medium", "per_page": 5}
        )
        data = resp.json()
        
        if data.get("videos"):
            video = data["videos"][0]
            # Get the HD file
            for vf in video.get("video_files", []):
                if vf.get("height", 0) >= 720 and vf.get("width", 0) < vf.get("height", 0):
                    download_url = vf["link"]
                    break
            else:
                download_url = video["video_files"][0]["link"]
            
            output_path = os.path.join(base_dir, "generated_assets", "background.mp4")
            print(f"  Downloading background video...")
            r = requests.get(download_url, stream=True)
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  Downloaded background video to {output_path}")
            return output_path
    except Exception as e:
        print(f"  Failed to download background: {e}")
    
    return None


def create_video_from_script(title: str, script: str) -> str | None:
    """
    Orchestrates the entire video production pipeline, now with a title reveal
    and karaoke-style word-by-word subtitles.
    """
    print("--- Production Agent Initialized (Karaoke Style) ---")

    # --- Audio Generation ---
    # Step 1a: Generate single audio file for the story WITH WORD TIMESTAMPS
    story_audio_info = audio_tools.generate_audio_with_word_timestamps(script, title)
    if not story_audio_info:
        print("Production failed: Could not generate story audio with timestamps.")
        return None
    
    story_audio_path = story_audio_info['audio_path']
    word_timestamps = story_audio_info['word_timestamps']

    # Step 1b: Generate audio for the title (as before)
    title_audio_info_list = audio_tools.text_to_speech_sentences(title, f"{title}_title")
    if not title_audio_info_list:
        print("Production failed: Could not generate title audio.")
        return None
    title_audio_clip_info = title_audio_info_list[0] # It's a list with one item

    # --- Visual Sourcing ---
    # Step 2: Get a background video (local or Pexels download)
    background_video_path = _get_background_video()
    if not background_video_path:
        print("Production failed: Could not retrieve background video.")
        return None

    # --- Video Assembly ---
    # Step 3: Assemble the final video using the new karaoke-style function
    final_video_path = editing_tools.create_final_video(
        title=title,
        background_video_path=background_video_path,
        story_audio_path=story_audio_path,
        word_timestamps=word_timestamps,
        title_audio_clip_info=title_audio_clip_info
    )

    if not final_video_path:
        print("Production failed: Could not create the final video.")
        return None

    print(f"--- Production Agent Finished Successfully! ---")
    print(f"Final video available at: {final_video_path}")
    return final_video_path

if __name__ == '__main__':
    from . import content_agent

    test_topic = "AITA for telling my brother his 'dream job' is a pyramid scheme?"
    print(f"--- Running Full Production Test for topic: '{test_topic}' ---")

    test_script = content_agent.generate_story_script(test_topic)

    if "Error:" not in test_script:
        create_video_from_script(test_topic, test_script)
    else:
        print(f"Could not run test: {test_script}")