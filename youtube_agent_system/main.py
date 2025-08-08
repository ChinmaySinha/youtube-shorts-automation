import argparse
from . import content_agent, production_agent, publishing_agent, config

def run_pipeline(topic: str):
    """
    Executes the full content generation pipeline from script to upload.

    This is the main orchestrator for the MVP. It follows a linear
    sequence of tasks, invoking each agent in turn.

    Args:
        topic: The topic for the video to be created.
    """
    print(f"--- STARTING YOUTUBE AUTOMATION PIPELINE ---")
    print(f"--- Topic: {topic} ---")

    # --- 1. Content Agent: Generate the script ---
    print("\n[PHASE 1/3] Calling Content Agent...")
    script = content_agent.generate_story_script(topic)
    if not script or "Error:" in script:
        print("Pipeline failed: Could not generate script.")
        print(f"Reason: {script}")
        return
    print("Content Agent finished successfully.")

    # --- 2. Production Agent: Create the video ---
    print("\n[PHASE 2/3] Calling Production Agent...")
    video_path = production_agent.create_video_from_script(topic, script)
    if not video_path:
        print("Pipeline failed: Could not produce video.")
        return
    print("Production Agent finished successfully.")

    # --- 3. Publishing Agent: Upload the video ---
    print("\n[PHASE 3/3] Calling Publishing Agent...")
    publishing_agent.publish_video(video_path, topic)
    print("Publishing Agent finished successfully.")

    print("\n--- YOUTUBE AUTOMATION PIPELINE COMPLETE ---")

if __name__ == '__main__':
    # --- Setup to run the script from the command line ---
    # To run, navigate to the root directory of the project (outside 'youtube_agent_system')
    # and run the command:
    # python -m youtube_agent_system.main --topic "your video topic here"
    #
    # If no topic is provided, it will use the default from config.py

    parser = argparse.ArgumentParser(description="Autonomous YouTube Content Generation System")
    parser.add_argument(
        "--topic",
        type=str,
        default=config.DEFAULT_TOPIC,
        help="The topic for the video to be generated."
    )
    args = parser.parse_args()

    run_pipeline(args.topic)
