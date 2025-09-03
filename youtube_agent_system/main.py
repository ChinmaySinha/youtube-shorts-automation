import os
import json
import random # <-- NEW: Import the random library
from . import production_agent, publishing_agent, strategy_agent, analytics_agent, config

VIDEO_LOG_FILE = os.path.join(config.LOGS_DIR, "published_videos_log.json")

def _load_video_log():
    """Loads the video log from the JSON file."""
    if not os.path.exists(VIDEO_LOG_FILE):
        return []
    try:
        with open(VIDEO_LOG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save_video_log(log_data):
    """Saves the video log to the JSON file."""
    with open(VIDEO_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=4)

def _log_new_video(video_id, topic, version_used): # <-- NEW: Track which version was used
    """Adds a new video to the log."""
    log_data = _load_video_log()
    log_data.append({"video_id": video_id, "topic": topic, "analyzed": False, "version": version_used})
    _save_video_log(log_data)

def run_intelligent_pipeline():
    """Executes the full, intelligent, learning pipeline."""
    print("--- 🚀 ADVANCED INTELLIGENT PIPELINE (v4) ---")

    # --- ANALYSIS STEP ---
    print("\n[PHASE 1/4] Running Analysis Step...")
    video_log = _load_video_log()
    
    videos_to_analyze = [video for video in video_log if not video.get("analyzed")]
    if videos_to_analyze:
        print(f"Found {len(videos_to_analyze)} unanalyzed video(s).")
        for video in videos_to_analyze:
            print(f"--- Analyzing video: {video['topic']} (ID: {video['video_id']}) ---")
            analytics_agent.analyze_video_performance(
                video_id=video["video_id"],
                topic=video["topic"]
            )
            video["analyzed"] = True
        _save_video_log(video_log)
    else:
        print("No new videos to analyze. Proceeding to content strategy.")

    # --- STRATEGY & CONTENT STEP ---
    print("\n[PHASE 2/4] Calling Advanced Strategy Agent to generate script...")
    
    # --- NEW: Randomly select which strategy version to run ---
    rand_num = random.random()
    if 0 <= rand_num < 0.16:
        strategy_version = 'a'
    elif 0.16 <= rand_num < 0.32:
        strategy_version = 'b'
    elif 0.32 <= rand_num < 0.48:
        strategy_version = 'c'
    elif 0.48 <= rand_num < 0.64:
        strategy_version = 'd'
    elif 0.64 <= rand_num < 0.80:
        strategy_version = 'e'
    else:
        strategy_version = 'f'
    
    print(f"--- Randomly selected Strategy Version: '{strategy_version.upper()}' ---")

    recent_topics = [video['topic'] for video in video_log[-3:]]
    
    strategy_result = strategy_agent.generate_optimized_script(
        recent_topics=recent_topics,
        version=strategy_version # <-- Pass the chosen version to the agent
    )
    if not strategy_result:
        print("Pipeline failed: Strategy Agent could not generate a script.")
        return

    script = strategy_result["script"]
    title = strategy_result["title"]

    # --- PRODUCTION STEP ---
    print("\n[PHASE 3/4] Calling Production Agent...")
    video_path = production_agent.create_video_from_script(title, script)
    if not video_path:
        print("Pipeline failed at Production stage.")
        return

    # --- PUBLISHING STEP ---
    print("\n[PHASE 4/4] Calling Publishing Agent...")
    new_video_id = publishing_agent.publish_video(video_path, title)
    if new_video_id:
        _log_new_video(new_video_id, title, strategy_version) # <-- Log which version was used
        print(f"Logged new video '{title}' with REAL ID '{new_video_id}' for future analysis.")
    else:
        print("Publishing failed. Video was not logged.")

    print("\n--- INTELLIGENT PIPELINE RUN COMPLETE ---")

if __name__ == '__main__':
    run_intelligent_pipeline()