import os
import json
from . import content_agent, production_agent, publishing_agent, strategy_agent, analytics_agent, config

# A simple JSON file to act as a database of our published videos.
# This will store video_id, topic, and whether it has been analyzed.
VIDEO_LOG_FILE = os.path.join(config.ASSETS_DIR, "published_videos_log.json")

def _load_video_log():
    """Loads the video log from the JSON file."""
    if not os.path.exists(VIDEO_LOG_FILE):
        return []
    with open(VIDEO_LOG_FILE, 'r') as f:
        return json.load(f)

def _save_video_log(log_data):
    """Saves the video log to the JSON file."""
    with open(VIDEO_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=4)

def _log_new_video(video_id, topic):
    """Adds a new video to the log."""
    log_data = _load_video_log()
    log_data.append({"video_id": video_id, "topic": topic, "analyzed": False})
    _save_video_log(log_data)

def run_learning_pipeline():
    """
    Executes the full, intelligent, learning pipeline.
    """
    print("--- 🧠 AUTONOMOUS LEARNING PIPELINE (v3) ---")

    # --- PRE-FLIGHT: ANALYSIS STEP ---
    # Find a published video that we haven't analyzed yet.
    print("\n[PHASE -1/5] Running Analysis Step...")
    video_log = _load_video_log()
    video_to_analyze = None
    for i, video in enumerate(video_log):
        if not video.get("analyzed"):
            video_to_analyze = video
            # Mark it as analyzed so we don't pick it again.
            video_log[i]["analyzed"] = True
            _save_video_log(video_log)
            break

    if video_to_analyze:
        analytics_agent.analyze_video_performance(
            video_id=video_to_analyze["video_id"],
            topic=video_to_analyze["topic"]
        )
    else:
        print("No new videos to analyze. Proceeding directly to content strategy.")

    # --- 0. STRATEGY STEP ---
    print("\n[PHASE 0/5] Calling Strategy Agent to decide topic...")
    topic = strategy_agent.decide_content_topic()
    if not topic:
        print("Pipeline failed: Strategy Agent could not decide on a topic.")
        return
    print(f"--- Topic Selected: {topic} ---")

    # --- 1. CONTENT STEP ---
    print("\n[PHASE 1/5] Calling Content Agent...")
    script = content_agent.generate_story_script(topic)
    if not script or "Error:" in script:
        print("Pipeline failed at Content stage.")
        return

    # --- 2. PRODUCTION STEP ---
    print("\n[PHASE 2/5] Calling Production Agent...")
    video_path = production_agent.create_video_from_script(topic, script)
    if not video_path:
        print("Pipeline failed at Production stage.")
        return

    # --- 3. PUBLISHING STEP ---
    print("\n[PHASE 3/5] Calling Publishing Agent...")
    # We need to capture the video_id returned by the publisher
    # For now, the publishing agent prints it. In a real system, it would return it.
    # We will simulate this by logging a placeholder ID for now.
    # TODO: Refactor publishing_agent to return the video ID.
    publishing_agent.publish_video(video_path, topic)

    # --- 4. POST-FLIGHT: LOGGING STEP ---
    print("\n[PHASE 4/5] Logging new video for future analysis...")
    # Simulating getting the video ID back. In a real scenario, the publish_video would return this.
    # For testing, we'll use a placeholder format.
    new_video_id_placeholder = f"placeholder_id_{random.randint(1000, 9999)}"
    _log_new_video(new_video_id_placeholder, topic)
    print(f"Logged new video '{topic}' with ID '{new_video_id_placeholder}'.")

    print("\n--- YOUTUBE LEARNING PIPELINE COMPLETE ---")

if __name__ == '__main__':
    # To run the new learning pipeline:
    # python -m youtube_agent_system.main
    import random
    run_learning_pipeline()
