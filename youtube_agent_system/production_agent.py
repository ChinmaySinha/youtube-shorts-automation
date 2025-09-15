# youtube_agent_system/production_agent.py
from .tools import audio_tools, video_tools, editing_tools

def create_video_from_script(title: str, script: str) -> str | None:
    """
    Orchestrates the entire video production pipeline, now with a title reveal
    and karaoke-style word-by-word subtitles.
    """
    print("--- 🎬 Production Agent Initialized (Karaoke Style) 🎬 ---")

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
    # Step 2: Get a background video (as before)
    background_video_path = r"youtube_agent_system\You literally have to Press Nothing to finish this track (Trackmania 2020).mp4"
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

    print(f"--- 🎬 Production Agent Finished Successfully! 🎬 ---")
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