import os
import json
from . import production_agent, publishing_agent, strategy_agent, analytics_agent, config
from . import intelligence_agent
from . import knowledge_base

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

def _log_new_video(video_id, topic, patterns_used: dict):
    """Adds a new video to the log with pattern tracking."""
    log_data = _load_video_log()
    log_data.append({
        "video_id": video_id,
        "topic": topic,
        "analyzed": False,
        "patterns_used": patterns_used
    })
    _save_video_log(log_data)


def run_intelligent_pipeline(skip_learning: bool = False):
    """
    Executes the full AUTONOMOUS INTELLIGENT pipeline.
    
    This pipeline:
    1. Learns from rival content using Gemini (Phase 0)
    2. Analyzes our past video performance (Phase 1)
    3. Uses learned patterns to generate optimized content (Phase 2)
    4. Produces the video (Phase 3)
    5. Publishes to YouTube (Phase 4)
    
    Args:
        skip_learning: If True, skips the rival analysis phase (for faster runs).
    """
    print("=" * 66)
    print("  AUTONOMOUS INTELLIGENT PIPELINE (v5 - Learning)")
    print("=" * 66)

    # --- PHASE 0: LEARNING PHASE (NEW) ---
    if not skip_learning:
        print("\n[PHASE 0/5] Learning from Rival Content...")
        try:
            ia = intelligence_agent.IntelligenceAgent()
            status = ia.get_status_report()
            
            # Check if we have enough data, if not run a full scan
            if status['knowledge_base']['rival_videos_analyzed'] < 5:
                print("Not enough rival data. Running full rival analysis...")
                ia.scan_and_analyze_rivals()
            else:
                print(f"Using existing knowledge ({status['knowledge_base']['rival_videos_analyzed']} rival videos analyzed)")
                
            # Show current recommendation
            rec = ia.get_content_recommendation()
            print(f"Current recommendation: {rec.get('content_category')} (Confidence: {rec.get('confidence', 0):.0%})")
        except Exception as e:
            print(f"Learning phase error (non-fatal): {e}")
            print("Continuing with available patterns...")
    else:
        print("\n[PHASE 0/5] [SKIP] Skipping learning phase (skip_learning=True)")

    # --- PHASE 1: ANALYSIS PHASE ---
    print("\n[PHASE 1/5] Running Analytics on Past Videos...")
    video_log = _load_video_log()
    
    videos_to_analyze = [video for video in video_log if not video.get("analyzed")]
    if videos_to_analyze:
        print(f"Found {len(videos_to_analyze)} unanalyzed video(s).")
        for video in videos_to_analyze:
            print(f"--- Analyzing video: {video['topic']} (ID: {video['video_id']}) ---")
            
            # Enhanced: Save insight with patterns used for correlation
            patterns_used = video.get('patterns_used', {})
            
            analytics_agent.analyze_video_performance(
                video_id=video["video_id"],
                topic=video["topic"]
            )
            video["analyzed"] = True
        _save_video_log(video_log)
    else:
        print("No new videos to analyze. Proceeding to content strategy.")

    # --- PHASE 2: INTELLIGENT STRATEGY & CONTENT ---
    print("\n[PHASE 2/5] Generating Content with Intelligent Strategy...")
    
    # Get recent topics to avoid repetition
    recent_topics = [video['topic'] for video in video_log[-3:]]
    
    # Use intelligent mode (learns from rivals)
    strategy_result = strategy_agent.generate_optimized_script(
        recent_topics=recent_topics,
        use_intelligence=True  # Use learned patterns
    )
    
    if not strategy_result:
        print("Pipeline failed: Strategy Agent could not generate a script.")
        return None

    script = strategy_result["script"]
    title = strategy_result["title"]
    patterns_used = strategy_result.get("patterns_used", {})
    content_category = patterns_used.get('content_category', 'AITA')  # For Shorts algorithm SEO
    
    print(f"\n[NOTE] Generated script for: {title}")
    print(f"[STATS] Patterns used: {patterns_used}")
    print(f"[CATEGORY] Content category: {content_category}")

    # --- PHASE 3: PRODUCTION ---
    print("\n[PHASE 3/5] Calling Production Agent...")
    video_path = production_agent.create_video_from_script(title, script)
    if not video_path:
        print("Pipeline failed at Production stage.")
        return None

    # --- PHASE 4: PUBLISHING (with Shorts algorithm optimization) ---
    print("\n[PHASE 4/5] Calling Publishing Agent...")
    new_video_id = publishing_agent.publish_video(
        video_path, title, content_category=content_category
    )
    if new_video_id:
        _log_new_video(new_video_id, title, patterns_used)
        print(f"[OK] Logged new video '{title}' with ID '{new_video_id}'")
    else:
        print("Publishing failed. Video was not logged.")
        return None

    # --- PHASE 5: SUMMARY ---
    print("\n[PHASE 5/5] Pipeline Summary...")
    stats = knowledge_base.get_knowledge_base_stats()
    
    print("\n" + "=" * 66)
    print("  [OK] INTELLIGENT PIPELINE COMPLETE")
    print("-" * 66)
    print(f"  Video Published: {title[:50]}...")
    print(f"  Video ID: {new_video_id}")
    print(f"  Patterns Used: {patterns_used.get('mode', 'unknown')} mode")
    print(f"  Knowledge Base: {stats['rival_videos_analyzed']} rival videos analyzed")
    print("=" * 66)
    
    return {
        "video_id": new_video_id,
        "title": title,
        "patterns_used": patterns_used,
        "video_path": video_path
    }


def run_learning_only():
    """
    Runs only the learning phase without producing a video.
    
    Use this to:
    - Initially populate the knowledge base with rival content
    - Update patterns after rival channels post new content
    - Debug the learning system
    """
    print("=" * 66)
    print("  LEARNING MODE (No Video Production)")
    print("=" * 66)
    
    ia = intelligence_agent.IntelligenceAgent()
    
    # Run full scan
    print("\n[1/3] Scanning and analyzing rival content...")
    scan_result = ia.scan_and_analyze_rivals(force_rescan=False)
    
    print("\n[2/3] Getting content recommendation...")
    recommendation = ia.get_content_recommendation()
    
    print("\n[3/3] Status Report:")
    status = ia.get_status_report()
    
    print("\n" + "=" * 66)
    print("  LEARNING COMPLETE")
    print("-" * 66)
    print(f"  Videos Analyzed: {status['knowledge_base']['rival_videos_analyzed']}")
    print(f"  Recommended Category: {recommendation.get('content_category', 'N/A')}")
    print(f"  Recommended Hook Style: {recommendation.get('hook_style', 'N/A')}")
    print(f"  Confidence: {recommendation.get('confidence', 0):.0%}")
    print(f"  Status: {status['system_status']}")
    print("=" * 66)
    
    return status


def run_quick_pipeline():
    """
    Runs a quick pipeline without the learning phase.
    
    Use this when:
    - You've already run learning recently
    - You want faster video production
    - You're testing the pipeline
    """
    return run_intelligent_pipeline(skip_learning=True)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'learn':
            run_learning_only()
        elif mode == 'quick':
            run_quick_pipeline()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python -m youtube_agent_system.main [learn|quick]")
    else:
        # Default: run full intelligent pipeline
        run_intelligent_pipeline()
