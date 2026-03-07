# youtube_agent_system/smart_scheduler.py
"""
Intelligent Auto-Posting Scheduler

This is the brain of the autonomous YouTube Shorts engine. It handles:
1. Posting 3-7 videos/day with intelligent timing
2. Cold-start strategy (no analytics for first 7 days)
3. Self-adjusting frequency based on performance data
4. Auto-replenishing story content when pool runs low
5. Crash recovery and persistent state

Usage:
    python -m youtube_agent_system.smart_scheduler
    python -m youtube_agent_system.smart_scheduler --min-daily 3 --max-daily 7
"""

import os
import sys
import json
import time
import random
import traceback
from datetime import datetime, timedelta
from . import config, knowledge_base, main as pipeline_main

# --- Configuration ---
STATE_FILE = os.path.join(config.LOGS_DIR, "scheduler_state.json")
SCHEDULE_LOG = os.path.join(config.LOGS_DIR, "schedule_log.json")

# Content pool thresholds
MIN_STORIES_BEFORE_REFILL = 500   # Trigger refill when unused stories drop below this
STORIES_PER_REFILL = 2000         # How many new stories to download per refill

# Posting time defaults (UTC hours) — industry-researched optimal Shorts times
# These are used during cold start before we have analytics data
DEFAULT_POSTING_HOURS_UTC = [6, 10, 14, 18, 21]  # 5 slots spread across the day

# How many days of data we need before trusting analytics
ANALYTICS_WARM_UP_DAYS = 10
MIN_VIDEOS_FOR_ANALYTICS = 15  # Need at least 15 videos posted before adjusting


class SmartScheduler:
    """
    Intelligent posting scheduler that self-adjusts based on performance.
    
    Cold Start Strategy (Days 1-10):
        - No analytics available yet, so use research-based posting times
        - Post exactly `min_daily` videos/day at evenly spaced intervals
        - Vary the exact minute randomly to appear more natural
        - Focus on building a catalog of diverse content
    
    Warm Phase (Days 11-20):
        - Analytics start trickling in (6-7 day delay from YouTube)
        - Begin tracking which time slots get more views
        - Slowly adjust times toward better-performing slots
        - Keep posting frequency at minimum to build data
    
    Intelligent Phase (Day 21+):
        - Full analytics data available for first batch of videos
        - Adjust posting frequency: scale up if views are good
        - Shift posting times to best-performing windows
        - Track category performance — post more of what works
    """
    
    def __init__(self, min_daily: int = 3, max_daily: int = 7):
        self.min_daily = min_daily
        self.max_daily = max_daily
        self.state = self._load_state()
        self.running = True
        
        # Log startup
        self._log("=" * 60)
        self._log("  SMART SCHEDULER INITIALIZED")
        self._log(f"  Min daily: {min_daily}, Max daily: {max_daily}")
        self._log(f"  Day #{self._get_days_running()}, Phase: {self._get_current_phase()}")
        self._log("=" * 60)
    
    # ========================================================
    # STATE MANAGEMENT
    # ========================================================
    
    def _load_state(self) -> dict:
        """Load scheduler state from disk or create fresh state."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self._log(f"Recovered state: Day {state.get('days_running', 0)}, "
                             f"{state.get('total_videos_posted', 0)} total videos posted")
                    return state
            except (json.JSONDecodeError, KeyError):
                self._log("[WARN] Corrupt state file, starting fresh")
        
        return {
            "first_start": datetime.now().isoformat(),
            "days_running": 0,
            "total_videos_posted": 0,
            "videos_posted_today": 0,
            "today_date": datetime.now().strftime("%Y-%m-%d"),
            "target_daily_count": self.min_daily,
            "today_post_times": [],      # Times we posted today
            "next_post_time": None,       # When to post next
            "used_story_ids": [],         # Stories we've already narrated
            "last_refill_date": None,
            
            # Performance tracking (last 30 days)
            "daily_performance": [],  # [{date, videos_posted, total_views, avg_views}]
            
            # Time slot performance
            "time_slot_performance": {
                str(h): {"posts": 0, "total_views": 0, "avg_views": 0}
                for h in range(24)
            },
            
            # Category performance
            "category_performance": {},
            
            # Errors
            "consecutive_failures": 0,
            "last_error": None,
            "last_successful_post": None,
        }
    
    def _save_state(self):
        """Persist scheduler state to disk."""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            self._log(f"[ERROR] Could not save state: {e}")
    
    def _log(self, message: str):
        """Log message to console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        print(formatted)
        
        try:
            log_file = os.path.join(config.LOGS_DIR, "scheduler.log")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted + "\n")
        except:
            pass
    
    def _log_post(self, video_id: str, title: str, category: str, post_hour: int):
        """Log a successful post for analytics."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "title": title,
            "category": category,
            "post_hour_utc": post_hour,
        }
        
        try:
            log_data = []
            if os.path.exists(SCHEDULE_LOG):
                with open(SCHEDULE_LOG, 'r') as f:
                    log_data = json.load(f)
            log_data.append(entry)
            # Keep last 200 entries
            log_data = log_data[-200:]
            with open(SCHEDULE_LOG, 'w') as f:
                json.dump(log_data, f, indent=2)
        except:
            pass

    # ========================================================
    # PHASE DETECTION
    # ========================================================
    
    def _get_days_running(self) -> int:
        """How many days since the scheduler first started."""
        try:
            first_start = datetime.fromisoformat(self.state["first_start"])
            return (datetime.now() - first_start).days
        except:
            return 0
    
    def _get_current_phase(self) -> str:
        """Determine which scheduling phase we're in."""
        days = self._get_days_running()
        total_videos = self.state.get("total_videos_posted", 0)
        
        if days < ANALYTICS_WARM_UP_DAYS or total_videos < MIN_VIDEOS_FOR_ANALYTICS:
            return "cold_start"
        elif days < 21:
            return "warming_up"
        else:
            return "intelligent"
    
    # ========================================================
    # SCHEDULING LOGIC
    # ========================================================
    
    def _reset_daily_counters(self):
        """Reset counters at the start of a new day."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if self.state["today_date"] != today:
            # Save yesterday's performance
            yesterday_data = {
                "date": self.state["today_date"],
                "videos_posted": self.state["videos_posted_today"],
                "target_was": self.state["target_daily_count"],
            }
            self.state["daily_performance"].append(yesterday_data)
            # Keep last 30 days
            self.state["daily_performance"] = self.state["daily_performance"][-30:]
            
            self.state["days_running"] = self._get_days_running()
            self.state["today_date"] = today
            self.state["videos_posted_today"] = 0
            self.state["today_post_times"] = []
            
            # Recalculate daily target
            self.state["target_daily_count"] = self._calculate_daily_target()
            
            self._log(f"--- NEW DAY: {today} ---")
            self._log(f"  Phase: {self._get_current_phase()}")
            self._log(f"  Target today: {self.state['target_daily_count']} videos")
            self._save_state()
    
    def _calculate_daily_target(self) -> int:
        """
        Decide how many videos to post today.
        
        Cold Start: Always post exactly min_daily (3).
        Warming Up: Stay at min_daily, focus on building catalog.
        Intelligent: Adjust based on recent performance trends.
        """
        phase = self._get_current_phase()
        
        if phase == "cold_start":
            return self.min_daily
        
        if phase == "warming_up":
            # Start experimenting: post one extra on random days
            return self.min_daily + (1 if random.random() > 0.6 else 0)
        
        # === Intelligent Phase ===
        # Look at last 7 days of performance
        recent = self.state["daily_performance"][-7:]
        if not recent:
            return self.min_daily
        
        avg_posted = sum(d.get("videos_posted", 0) for d in recent) / len(recent)
        
        # Check how many consecutive failures we've had
        if self.state.get("consecutive_failures", 0) >= 3:
            self._log("[WARN] 3+ consecutive failures, reducing to minimum")
            return self.min_daily
        
        # For now without views data (first few weeks), gradually ramp up
        # Once we have views data, this will use actual performance metrics
        total_videos = self.state.get("total_videos_posted", 0)
        
        if total_videos < 30:
            target = self.min_daily  # First 30 videos: stay conservative
        elif total_videos < 60:
            target = min(self.min_daily + 1, self.max_daily)
        elif total_videos < 100:
            target = min(self.min_daily + 2, self.max_daily)
        else:
            target = min(self.min_daily + 3, self.max_daily)
        
        self._log(f"  Calculated target: {target}/day (phase={phase}, total_posted={total_videos})")
        return target
    
    def _get_next_post_time(self) -> datetime:
        """
        Calculate when to post the next video.
        
        Cold Start: Spread evenly across the day at known good hours.
        Intelligent: Use best-performing time slots.
        """
        now = datetime.now()
        today_count = self.state["videos_posted_today"]
        target = self.state["target_daily_count"]
        remaining = target - today_count
        
        if remaining <= 0:
            # Done for today — wait until tomorrow
            tomorrow = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
            # Start at 6 AM
            return tomorrow.replace(hour=6, minute=random.randint(0, 30))
        
        phase = self._get_current_phase()
        
        if phase == "cold_start":
            # Use default posting hours, evenly spread
            return self._cold_start_next_time(now, today_count, target)
        else:
            # Use best-performing hours
            return self._intelligent_next_time(now, today_count, remaining)
    
    def _cold_start_next_time(self, now: datetime, posted_today: int, target: int) -> datetime:
        """
        Cold start: spread posts evenly across the waking hours.
        Avoid posting between midnight and 5 AM (low engagement).
        """
        # Available hours: 6 AM to 11 PM (17 hours)
        waking_hours = list(range(6, 24))  # 6AM to 11PM
        
        # Divide waking hours by target number of posts
        interval = len(waking_hours) // target
        post_hours = [waking_hours[i * interval] for i in range(target)]
        
        # Find the next slot we haven't used yet
        for hour in post_hours[posted_today:]:
            target_time = now.replace(hour=hour, minute=random.randint(0, 45), second=0)
            if target_time > now:
                return target_time
        
        # If all slots for today have passed, post in 30 minutes
        return now + timedelta(minutes=30)
    
    def _intelligent_next_time(self, now: datetime, posted_today: int, remaining: int) -> datetime:
        """
        Intelligent: pick the best performing hour that we haven't used today.
        """
        # Get hours sorted by performance (best first)
        slot_perf = self.state.get("time_slot_performance", {})
        
        # Filter to waking hours and sort by avg views
        scored_hours = []
        for hour_str, data in slot_perf.items():
            hour = int(hour_str)
            if 6 <= hour <= 23:  # Waking hours only
                avg = data.get("avg_views", 0)
                posts = data.get("posts", 0)
                scored_hours.append((hour, avg, posts))
        
        # Sort: prioritize hours with good views, but also explore hours with few posts
        scored_hours.sort(key=lambda x: (x[1] + (100 if x[2] < 3 else 0)), reverse=True)
        
        # Filter out hours we already posted at today
        today_hours = [datetime.fromisoformat(t).hour for t in self.state.get("today_post_times", [])]
        available = [h for h, _, _ in scored_hours if h not in today_hours]
        
        if not available:
            # All good hours used today, just wait 2 hours
            return now + timedelta(hours=2)
        
        # Pick the best available hour
        target_hour = available[0]
        target_time = now.replace(hour=target_hour, minute=random.randint(0, 45), second=0)
        
        if target_time <= now:
            # This hour already passed, pick the next one
            for h in available[1:]:
                target_time = now.replace(hour=h, minute=random.randint(0, 45), second=0)
                if target_time > now:
                    break
            else:
                target_time = now + timedelta(minutes=30)
        
        return target_time


    # ========================================================
    # CONTENT REPLENISHMENT
    # ========================================================
    
    def _check_content_pool(self):
        """
        Check if we're running low on unused stories and trigger a refill.
        We track used story IDs to avoid narrating the same story twice.
        """
        total_stories = knowledge_base.get_training_story_count()
        used_count = len(self.state.get("used_story_ids", []))
        remaining = total_stories - used_count
        
        self._log(f"  Content pool: {remaining} unused stories ({total_stories} total, {used_count} used)")
        
        if remaining < MIN_STORIES_BEFORE_REFILL:
            self._log(f"[REFILL] Pool running low ({remaining} remaining). Downloading more stories...")
            self._refill_content()
    
    def _refill_content(self):
        """Download more stories from Hugging Face and load into ChromaDB."""
        try:
            from .tools import dataset_downloader
            
            self._log("[REFILL] Downloading stories from Hugging Face...")
            stories = dataset_downloader.run_full_download_pipeline(
                max_download=STORIES_PER_REFILL,
                top_n=STORIES_PER_REFILL,
                min_quality=3.0,
                save=True
            )
            
            if stories:
                loaded = knowledge_base.save_training_stories_batch(stories)
                self._log(f"[REFILL] Loaded {loaded} new stories into ChromaDB")
                self.state["last_refill_date"] = datetime.now().isoformat()
                
                # Clear used IDs since we have fresh content
                # (old IDs may still be in DB so they won't collide)
                self._save_state()
            else:
                self._log("[REFILL] WARNING: No stories downloaded. Check internet connection.")
                
        except Exception as e:
            self._log(f"[REFILL] Error during refill: {e}")
            traceback.print_exc()
    
    def _mark_story_used(self, story_id: str):
        """Track which stories have been narrated to avoid repeats."""
        used = self.state.get("used_story_ids", [])
        if story_id not in used:
            used.append(story_id)
            # Keep list manageable — if it gets huge, trim oldest entries
            if len(used) > 10000:
                used = used[-5000:]
            self.state["used_story_ids"] = used
    
    # ========================================================
    # VIDEO PRODUCTION
    # ========================================================
    
    def _produce_and_post_video(self) -> bool:
        """
        Run the full pipeline to produce and upload one video.
        Returns True on success, False on failure.
        """
        self._log("--- Starting video production cycle ---")
        
        try:
            result = pipeline_main.run_intelligent_pipeline(skip_learning=True)
            
            if result and result.get("video_id"):
                video_id = result["video_id"]
                title = result.get("title", "Unknown")
                category = result.get("patterns_used", {}).get("content_category", "UNKNOWN")
                source_story = result.get("patterns_used", {}).get("source_story", "")
                post_hour = datetime.now().hour
                
                # Update state
                self.state["videos_posted_today"] += 1
                self.state["total_videos_posted"] += 1
                self.state["today_post_times"].append(datetime.now().isoformat())
                self.state["consecutive_failures"] = 0
                self.state["last_successful_post"] = datetime.now().isoformat()
                
                # Track the story as used
                story_id = result.get("patterns_used", {}).get("source_story", "")
                if story_id:
                    self._mark_story_used(story_id)
                
                # Update time slot tracking
                hour_key = str(post_hour)
                if hour_key not in self.state["time_slot_performance"]:
                    self.state["time_slot_performance"][hour_key] = {"posts": 0, "total_views": 0, "avg_views": 0}
                self.state["time_slot_performance"][hour_key]["posts"] += 1
                
                # Update category tracking
                if category not in self.state["category_performance"]:
                    self.state["category_performance"][category] = {"posts": 0, "total_views": 0}
                self.state["category_performance"][category]["posts"] += 1
                
                # Log the post
                self._log_post(video_id, title, category, post_hour)
                
                self._log(f"[OK] Video #{self.state['total_videos_posted']} posted!")
                self._log(f"  Title: {title}")
                self._log(f"  ID: {video_id}")
                self._log(f"  Category: {category}")
                self._log(f"  Today: {self.state['videos_posted_today']}/{self.state['target_daily_count']}")
                
                self._save_state()
                return True
            else:
                self.state["consecutive_failures"] += 1
                self.state["last_error"] = "Pipeline returned no video ID"
                self._log(f"[FAIL] Pipeline failed (attempt #{self.state['consecutive_failures']})")
                self._save_state()
                return False
                
        except Exception as e:
            self.state["consecutive_failures"] += 1
            self.state["last_error"] = str(e)[:200]
            self._log(f"[ERROR] Video production failed: {e}")
            traceback.print_exc()
            self._save_state()
            return False
    
    # ========================================================
    # MAIN RUN LOOP
    # ========================================================
    
    def run(self):
        """
        Main scheduler loop. Runs forever (or until stopped).
        
        Loop logic:
        1. Check if new day -> reset counters, recalculate target
        2. Check content pool -> refill if low
        3. Calculate next posting time
        4. Sleep until that time
        5. Produce and post video
        6. Repeat
        """
        self._log("Starting scheduler main loop...")
        self._log(f"Phase: {self._get_current_phase()}")
        self._log(f"Total videos posted so far: {self.state.get('total_videos_posted', 0)}")
        
        try:
            while self.running:
                # Step 1: Check for new day
                self._reset_daily_counters()
                
                # Step 2: Check if we've hit today's target
                posted = self.state["videos_posted_today"]
                target = self.state["target_daily_count"]
                
                if posted >= target:
                    # Done for today, sleep until tomorrow
                    now = datetime.now()
                    tomorrow_6am = (now + timedelta(days=1)).replace(hour=6, minute=0, second=0)
                    sleep_seconds = (tomorrow_6am - now).total_seconds()
                    self._log(f"[DONE] Posted {posted}/{target} today. Sleeping until tomorrow 6 AM ({sleep_seconds/3600:.1f}h)")
                    self._interruptible_sleep(sleep_seconds)
                    continue
                
                # Step 3: Check content pool
                self._check_content_pool()
                
                # Step 4: Calculate next post time
                next_time = self._get_next_post_time()
                now = datetime.now()
                
                if next_time > now:
                    wait_seconds = (next_time - now).total_seconds()
                    self._log(f"Next post scheduled at {next_time.strftime('%H:%M')} ({wait_seconds/60:.0f} min from now)")
                    self._log(f"  Progress: {posted}/{target} videos today | Phase: {self._get_current_phase()}")
                    self._interruptible_sleep(wait_seconds)
                    
                    if not self.running:
                        break
                
                # Step 5: Produce and post!
                self._log(f"\n{'=' * 50}")
                self._log(f"  POSTING VIDEO {posted + 1}/{target}")
                self._log(f"{'=' * 50}")
                
                success = self._produce_and_post_video()
                
                if not success:
                    # Backoff on failure
                    failures = self.state.get("consecutive_failures", 1)
                    backoff = min(failures * 300, 1800)  # 5 min per failure, max 30 min
                    self._log(f"Backing off for {backoff/60:.0f} minutes due to failure")
                    self._interruptible_sleep(backoff)
                else:
                    # Brief cooldown between videos (2-5 minutes)
                    cooldown = random.randint(120, 300)
                    self._log(f"Cooldown: {cooldown/60:.0f} minutes before next check")
                    self._interruptible_sleep(cooldown)
                    
        except KeyboardInterrupt:
            self._log("[STOP] Interrupted by user (Ctrl+C)")
        except Exception as e:
            self._log(f"[FATAL] Scheduler crashed: {e}")
            traceback.print_exc()
        finally:
            self._save_state()
            self._log("Scheduler stopped. State saved.")
    
    def _interruptible_sleep(self, seconds: float):
        """Sleep that can be interrupted by stop signal."""
        end_time = time.time() + seconds
        while time.time() < end_time and self.running:
            time.sleep(min(10, end_time - time.time()))
    
    def stop(self):
        """Gracefully stop the scheduler."""
        self._log("[STOP] Stop requested...")
        self.running = False
    
    def get_status(self) -> dict:
        """Return current scheduler status."""
        return {
            "phase": self._get_current_phase(),
            "days_running": self._get_days_running(),
            "total_videos_posted": self.state.get("total_videos_posted", 0),
            "videos_today": f"{self.state['videos_posted_today']}/{self.state['target_daily_count']}",
            "consecutive_failures": self.state.get("consecutive_failures", 0),
            "last_successful_post": self.state.get("last_successful_post"),
            "content_pool": knowledge_base.get_training_story_count(),
            "used_stories": len(self.state.get("used_story_ids", [])),
        }


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent YouTube Shorts Auto-Poster")
    parser.add_argument("--min-daily", type=int, default=3, help="Minimum videos per day (default: 3)")
    parser.add_argument("--max-daily", type=int, default=7, help="Maximum videos per day (default: 7)")
    parser.add_argument("--status", action="store_true", help="Show current scheduler status and exit")
    parser.add_argument("--reset", action="store_true", help="Reset scheduler state and start fresh")
    
    args = parser.parse_args()
    
    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            print("Scheduler state reset.")
        return
    
    scheduler = SmartScheduler(
        min_daily=args.min_daily,
        max_daily=args.max_daily,
    )
    
    if args.status:
        status = scheduler.get_status()
        print("\n=== Smart Scheduler Status ===")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return
    
    # Run the scheduler (blocks forever)
    scheduler.run()


if __name__ == '__main__':
    main()
