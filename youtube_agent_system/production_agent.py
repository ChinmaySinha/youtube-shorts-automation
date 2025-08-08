from .tools import audio_tools, video_tools, editing_tools

def create_video_from_script(topic: str, script: str) -> str | None:
    """
    Orchestrates the entire video production pipeline.

    This function embodies the ProductionAgent. It takes a topic and a script,
    then uses the various tools to generate audio, source video, and
    assemble the final product.

    Args:
        topic: The central topic of the video.
        script: The narrative script for the video.

    Returns:
        The file path of the final rendered video, or None if any step fails.
    """
    print("--- 🎬 Production Agent Initialized 🎬 ---")

    # Step 1: Generate audio from the script
    # This returns a list of dictionaries with audio paths, durations, and text
    audio_clips_info = audio_tools.text_to_speech_sentences(script, topic)
    if not audio_clips_info:
        print("Production failed: Could not generate audio.")
        return None

    # Step 2: Get a background video based on the topic
    background_video_path = video_tools.get_background_video(topic)
    if not background_video_path:
        print("Production failed: Could not retrieve background video.")
        return None

    # Step 3: Assemble the final video
    # This combines the video, audio, and subtitles
    final_video_path = editing_tools.create_final_video(
        topic,
        background_video_path,
        audio_clips_info
    )

    if not final_video_path:
        print("Production failed: Could not create the final video.")
        return None

    print(f"--- 🎬 Production Agent Finished Successfully! 🎬 ---")
    print(f"Final video available at: {final_video_path}")
    return final_video_path

if __name__ == '__main__':
    # To test this agent, we need a script first.
    # Let's use the content_agent to generate one.
    from . import content_agent

    test_topic = "a single leaf in a storm"
    print(f"--- Running Full Production Test for topic: '{test_topic}' ---")

    # Ensure you have a .env file with GROQ_API_KEY and PEXELS_API_KEY
    test_script = content_agent.generate_story_script(test_topic)

    if "Error:" not in test_script:
        create_video_from_script(test_topic, test_script)
    else:
        print(f"Could not run test: {test_script}")
