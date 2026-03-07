# youtube_agent_system/post_gate.py
"""
GitHub Actions Gate Script

Decides whether to produce a video NOW or skip this slot.
Called before each pipeline run in GitHub Actions.

Exit codes:
    0 = POST (proceed with video production)
    1 = SKIP (don't post this time)

Logic:
    - Cold start (days 0-10): post exactly 3/day
    - Warming (days 11-20): post 3-4/day
    - Intelligent (21+): post 3-7/day based on track record
"""

import os
import sys
import json
from datetime import datetime, timedelta

STATE_FILE = os.path.join(os.path.dirname(__file__), "logs", "ga_scheduler_state.json")

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "first_run": datetime.now().isoformat(),
        "total_videos": 0,
        "today_date": "",
        "today_count": 0,
        "daily_target": 3,
        "consecutive_failures": 0,
        "daily_history": [],  # [{date, count}]
    }

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def get_days_running(state: dict) -> int:
    try:
        first = datetime.fromisoformat(state["first_run"])
        return (datetime.now() - first).days
    except:
        return 0

def calculate_target(state: dict) -> int:
    """How many videos should we post today?"""
    days = get_days_running(state)
    total = state.get("total_videos", 0)
    failures = state.get("consecutive_failures", 0)
    
    # If crashing a lot, back off
    if failures >= 3:
        return 3
    
    # Cold start: exactly 3
    if days < 10 or total < 15:
        return 3
    
    # Warming: 3-4
    if days < 21 or total < 40:
        return 4
    
    # Intelligent: ramp up based on catalog size
    if total < 60:
        return 4
    elif total < 100:
        return 5
    elif total < 150:
        return 6
    else:
        return 7

def should_post() -> bool:
    """Main decision: should we post right now?"""
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Reset daily counter if new day
    if state["today_date"] != today:
        # Log yesterday
        if state["today_date"]:
            state["daily_history"].append({
                "date": state["today_date"],
                "count": state["today_count"],
            })
            state["daily_history"] = state["daily_history"][-30:]
        
        state["today_date"] = today
        state["today_count"] = 0
        state["daily_target"] = calculate_target(state)
        save_state(state)
    
    posted = state["today_count"]
    target = state["daily_target"]
    
    print(f"[GATE] Day #{get_days_running(state)} | "
          f"Today: {posted}/{target} | "
          f"Total: {state['total_videos']} | "
          f"Failures: {state['consecutive_failures']}")
    
    if posted >= target:
        print(f"[GATE] SKIP - Already posted {posted}/{target} today")
        return False
    
    print(f"[GATE] POST - Slot {posted + 1}/{target}")
    return True

def record_success():
    """Call after a successful post."""
    state = load_state()
    state["today_count"] += 1
    state["total_videos"] += 1
    state["consecutive_failures"] = 0
    save_state(state)
    print(f"[GATE] Recorded success. Total: {state['total_videos']}, Today: {state['today_count']}")

def record_failure():
    """Call after a failed post."""
    state = load_state()
    state["consecutive_failures"] += 1
    save_state(state)
    print(f"[GATE] Recorded failure #{state['consecutive_failures']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "success":
            record_success()
        elif sys.argv[1] == "failure":
            record_failure()
        elif sys.argv[1] == "status":
            state = load_state()
            print(json.dumps(state, indent=2))
        sys.exit(0)
    
    # Default: check gate
    if should_post():
        sys.exit(0)  # 0 = proceed
    else:
        sys.exit(1)  # 1 = skip
