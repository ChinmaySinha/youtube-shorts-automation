import os
import json
import random
from . import production_agent, publishing_agent, strategy_agent, analytics_agent, config

# A simple JSON file to act as a database of our published videos.
VIDEO_LOG_FILE = os.path.join(config.ASSETS_DIR, "published_videos_log.json")

def _load_video_log():
    """Loads the video log from the JSON file."""
    if not os.path.exists(VIDEO_LOG_FILE):
        return []
    try:
        with open(VIDEO_LOG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return [] # Return empty list if file is empty or corrupt

def _save_video_log(log_data):
    """Saves the video log to the JSON file."""
    with open(VIDEO_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=4)

def _log_new_video(video_id, topic):
    """Adds a new video to the log."""
    log_data = _load_video_log()
    log_data.append({"video_id": video_id, "topic": topic, "analyzed": False})
    _save_video_log(log_data)

def run_intelligent_pipeline():
    """
    Executes the full, intelligent, learning pipeline (Phase 4).
    The StrategyAgent now generates the script directly.
    """
    print("--- 🚀 ADVANCED INTELLIGENT PIPELINE (v4) ---")

    # --- ANALYSIS STEP ---
    print("\n[PHASE 1/4] Running Analysis Step...")
    video_log = _load_video_log()
    video_to_analyze = next((video for i, video in enumerate(video_log) if not video.get("analyzed")), None)

    if video_to_analyze:
        print(f"Found unanalyzed video: {video_to_analyze['topic']}")
        analytics_agent.analyze_video_performance(
            video_id=video_to_analyze["video_id"],
            topic=video_to_analyze["topic"]
        )
        # Mark as analyzed
        for video in video_log:
            if video["video_id"] == video_to_analyze["video_id"]:
                video["analyzed"] = True
                break
        _save_video_log(video_log)
    else:
        print("No new videos to analyze. Proceeding directly to content strategy.")

    # --- STRATEGY & CONTENT STEP ---
    print("\n[PHASE 2/4] Calling Advanced Strategy Agent to generate script...")
    strategy_result = strategy_agent.generate_optimized_script()
    if not strategy_result:
        print("Pipeline failed: Strategy Agent could not generate a script.")
        return

    script = strategy_result["script"]
    title = strategy_result["title"]
    print(f"--- Strategy Complete. New Title: '{title}' ---")

    # --- PRODUCTION STEP ---
    print("\n[PHASE 3/4] Calling Production Agent...")
    video_path = production_agent.create_video_from_script(title, script) # Use the new title for file naming
    if not video_path:
        print("Pipeline failed at Production stage.")
        return

    # --- PUBLISHING STEP ---
    print("\n[PHASE 4/4] Calling Publishing Agent...")
    # NOTE: The publishing agent will generate its own SEO from the topic.
    # We pass the generated title as the 'topic' for context.
    publishing_agent.publish_video(video_path, title)

    # In a real system, we'd get the new video_id back from the publisher.
    new_video_id_placeholder = f"placeholder_id_{random.randint(10000, 99999)}"
    _log_new_video(new_video_id_placeholder, title)
    print(f"Logged new video '{title}' with ID '{new_video_id_placeholder}' for future analysis.")

    print("\n--- INTELLIGENT PIPELINE RUN COMPLETE ---")

if __name__ == '__main__':
    run_intelligent_pipeline()
