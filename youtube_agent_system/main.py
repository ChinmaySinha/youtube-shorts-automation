from . import content_agent, production_agent, publishing_agent, strategy_agent

def run_automated_pipeline():
    """
    Executes the full, automated content generation pipeline.

    This version is fully autonomous. It starts by calling the StrategyAgent
    to decide on a topic, then proceeds with the rest of the pipeline.
    """
    # --- 0. Strategy Agent: Decide on a topic ---
    print("--- AUTONOMOUS YOUTUBE AUTOMATION PIPELINE ---")
    print("\n[PHASE 0/4] Calling Strategy Agent to decide topic...")
    topic = strategy_agent.decide_content_topic()
    if not topic:
        print("Pipeline failed: Strategy Agent could not decide on a topic.")
        return
    print(f"--- Topic Selected: {topic} ---")

    # --- 1. Content Agent: Generate the script ---
    print("\n[PHASE 1/4] Calling Content Agent...")
    script = content_agent.generate_story_script(topic)
    if not script or "Error:" in script:
        print("Pipeline failed: Could not generate script.")
        print(f"Reason: {script}")
        return
    print("Content Agent finished successfully.")

    # --- 2. Production Agent: Create the video ---
    print("\n[PHASE 2/4] Calling Production Agent...")
    # The production agent no longer needs the topic for video search
    video_path = production_agent.create_video_from_script(topic, script)
    if not video_path:
        print("Pipeline failed: Could not produce video.")
        return
    print("Production Agent finished successfully.")

    # --- 3. Publishing Agent: Upload the video ---
    print("\n[PHASE 3/4] Calling Publishing Agent...")
    publishing_agent.publish_video(video_path, topic)
    print("Publishing Agent finished successfully.")

    print("\n--- YOUTUBE AUTOMATION PIPELINE COMPLETE ---")

if __name__ == '__main__':
    # --- To run the new automated pipeline ---
    # Navigate to the root directory of the project (outside 'youtube_agent_system')
    # and run the command:
    # python -m youtube_agent_system.main

    run_automated_pipeline()
