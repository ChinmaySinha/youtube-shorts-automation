from .tools import audio_tools, video_tools, editing_tools

def create_video_from_script(title: str, script: str) -> str | None:
    """
    Orchestrates the entire video production pipeline, now with a title reveal.

    This function embodies the ProductionAgent. It takes a title and a script,
    then uses the various tools to generate audio for both, source a video,
    and assemble the final product.

    Args:
        title: The title of the video.
        script: The narrative script for the video.

    Returns:
        The file path of the final rendered video, or None if any step fails.
    """
    print("--- 🎬 Production Agent Initialized (with Title Reveal) 🎬 ---")

    # --- Audio Generation ---
    # Step 1a: Generate audio for the main story script
    story_audio_clips_info = audio_tools.text_to_speech_sentences(script, title)
    if not story_audio_clips_info:
        print("Production failed: Could not generate story audio.")
        return None

    # Step 1b: Generate a single audio clip for the title
    # We treat the title as a single sentence.
    title_audio_info = audio_tools.text_to_speech_sentences(title, f"{title}_title")
    if not title_audio_info:
        print("Production failed: Could not generate title audio.")
        return None

    # --- Visual Sourcing ---
    # Step 2: Get a background video
    #background_video_path = video_tools.get_background_video()
    background_video_path = r"youtube_agent_system\Minecraft Parkour Gameplay NO COPYRIGHT (Vertical) - Orbital - No Copyright Gameplay (1080p, h264).mp4"
    if not background_video_path:
        print("Production failed: Could not retrieve background video.")
        return None

    # --- Video Assembly ---
    # Step 3: Assemble the final video, now passing the title info as well
    final_video_path = editing_tools.create_final_video(
        title=title,
        background_video_path=background_video_path,
        story_audio_clips_info=story_audio_clips_info,
        title_audio_clip_info=title_audio_info[0] # It's a list with one item
    )

    if not final_video_path:
        print("Production failed: Could not create the final video.")
        return None

    print(f"--- 🎬 Production Agent Finished Successfully! 🎬 ---")
    print(f"Final video available at: {final_video_path}")
    return final_video_path

if __name__ == '__main__':
    # To test this agent, we need a script first.
    from . import content_agent

    test_topic = "AITA for swapping my sister's wedding cake with a foam replica?"
    print(f"--- Running Full Production Test for topic: '{test_topic}' ---")

    test_script = content_agent.generate_story_script(test_topic)

    if "Error:" not in test_script:
        create_video_from_script(test_topic, test_script)
    else:
        print(f"Could not run test: {test_script}")