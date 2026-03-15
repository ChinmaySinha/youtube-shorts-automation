#!/usr/bin/env python
"""
YouTube Shorts Automation - Kaggle Pipeline
============================================
SETUP:
1. Create TWO Kaggle Datasets:
   a) "youtube-pipeline-code" - upload the youtube_agent_system/ folder
   b) "youtube-bg-video" - upload your Trackmania .mp4
2. Create a Kaggle Notebook, paste this script
3. Add both datasets to notebook (right panel > Add Data)
4. Add Kaggle Secrets (Settings > Secrets):
   - GROQ_API_KEY, PEXELS_API_KEY, YOUTUBE_CHANNEL_ID
   - ELEVENLABS_API_KEY, GEMINI_API_KEY
   - YOUTUBE_TOKEN_B64, CLIENT_SECRETS_B64
5. Enable Internet (Settings > Internet > On)
6. Run All, then schedule daily
"""

import subprocess
import sys
import os
import base64
import shutil

# ============================================
# STEP 1: Install dependencies
# ============================================
print("=" * 60)
print("  STEP 1: Installing dependencies")
print("=" * 60)

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
    "groq", "edge-tts", "moviepy==1.0.3", "python-dotenv",
    "whisper-timestamped", "chromadb", "google-auth",
    "google-auth-oauthlib", "google-api-python-client",
    "datasets", "yt-dlp", "praw", "requests", "Pillow",
    "elevenlabs>=1.0.0", "gTTS"
])

os.system("apt-get update -qq && apt-get install -y -qq ffmpeg > /dev/null 2>&1")
print("Dependencies installed!")

# ============================================
# STEP 2: Clone the repo (public)
# ============================================
print("\n" + "=" * 60)
print("  STEP 2: Cloning repository")
print("=" * 60)

REPO_URL = "https://github.com/ChinmaySinha/youtube-shorts-automation.git"
WORK_DIR = "/kaggle/working/youtube-shorts-automation"
agent_dir = os.path.join(WORK_DIR, "youtube_agent_system")

if os.path.exists(WORK_DIR):
    subprocess.run(["git", "pull"], cwd=WORK_DIR)
else:
    subprocess.run(["git", "clone", REPO_URL, WORK_DIR], check=True)

os.chdir(WORK_DIR)
print(f"Working directory: {os.getcwd()}")

# ============================================
# STEP 3: Restore credentials from Kaggle Secrets
# ============================================
print("\n" + "=" * 60)
print("  STEP 3: Setting up credentials")
print("=" * 60)

from kaggle_secrets import UserSecretsClient
secrets = UserSecretsClient()

# Get API keys
groq_key = secrets.get_secret("GROQ_API_KEY")
pexels_key = secrets.get_secret("PEXELS_API_KEY")
channel_id = secrets.get_secret("YOUTUBE_CHANNEL_ID")

# Try optional keys
try:
    elevenlabs_key = secrets.get_secret("ELEVENLABS_API_KEY")
except:
    elevenlabs_key = ""

try:
    gemini_key = secrets.get_secret("GEMINI_API_KEY")
except:
    gemini_key = ""

try:
    nvidia_key = secrets.get_secret("NVIDIA_API_KEY")
except:
    nvidia_key = ""

# Write .env file
env_content = f"""# Groq API for Language Model
GROQ_API_KEY={groq_key}

# Pexels API for background videos
PEXELS_API_KEY={pexels_key}

# YouTube Channel ID
YOUTUBE_CHANNEL_ID={channel_id}

# ElevenLabs API
ELEVENLABS_API_KEY={elevenlabs_key}

# Gemini API
GEMINI_API_KEY={gemini_key}

# NVIDIA API (Nemotron LLM + Riva TTS)
NVIDIA_API_KEY={nvidia_key}
"""

env_path = os.path.join(WORK_DIR, "youtube_agent_system", ".env")
with open(env_path, 'w') as f:
    f.write(env_content)
print(f"Written .env to {env_path}")

# Decode and write YouTube OAuth token
try:
    token_b64 = secrets.get_secret("YOUTUBE_TOKEN_B64")
    token_data = base64.b64decode(token_b64)
    token_path = os.path.join(WORK_DIR, "youtube_agent_system", "token.pickle")
    with open(token_path, 'wb') as f:
        f.write(token_data)
    print(f"Written token.pickle ({len(token_data)} bytes)")
except Exception as e:
    print(f"WARNING: Could not restore token.pickle: {e}")

# Decode and write client_secrets.json
try:
    client_b64 = secrets.get_secret("CLIENT_SECRETS_B64")
    client_data = base64.b64decode(client_b64)
    client_path = os.path.join(WORK_DIR, "youtube_agent_system", "client_secrets.json")
    with open(client_path, 'wb') as f:
        f.write(client_data)
    print(f"Written client_secrets.json ({len(client_data)} bytes)")
except Exception as e:
    print(f"WARNING: Could not restore client_secrets.json: {e}")

# ============================================
# STEP 4: Link background video
# ============================================
print("\n" + "=" * 60)
print("  STEP 4: Setting up background video")
print("=" * 60)

# Check for video in Kaggle dataset
bg_video_dir = "/kaggle/input/youtube-bg-video"
agent_dir = os.path.join(WORK_DIR, "youtube_agent_system")

# Look for any .mp4 in the dataset
bg_found = False
if os.path.exists(bg_video_dir):
    for f in os.listdir(bg_video_dir):
        if f.endswith('.mp4'):
            src = os.path.join(bg_video_dir, f)
            dst = os.path.join(agent_dir, f)
            if not os.path.exists(dst):
                os.symlink(src, dst)
            print(f"Linked background video: {f}")
            bg_found = True
            break

# Also check if video exists in repo
if not bg_found:
    for f in os.listdir(agent_dir):
        if f.endswith('.mp4') and 'generated' not in f.lower():
            print(f"Found background video in repo: {f}")
            bg_found = True
            break

if not bg_found:
    print("WARNING: No background video found!")
    print("Please add your video as a Kaggle dataset named 'youtube-bg-video'")

# ============================================
# STEP 5: Setup directories
# ============================================
os.makedirs(os.path.join(agent_dir, "generated_assets"), exist_ok=True)
os.makedirs(os.path.join(agent_dir, "logs"), exist_ok=True)
os.makedirs(os.path.join(agent_dir, "fonts"), exist_ok=True)
os.makedirs(os.path.join(agent_dir, "chroma_db"), exist_ok=True)

# ============================================
# STEP 6: Run the pipeline (3 videos per run)
# ============================================
# Kaggle scheduler runs once/day, so we loop 3 times
# to produce 3 videos in a single session.

VIDEOS_PER_RUN = 7  # ~20 min each = ~2.3 hrs, well under Kaggle's 9hr limit
sys.path.insert(0, WORK_DIR)
successes = 0

for i in range(1, VIDEOS_PER_RUN + 1):
    print("\n" + "=" * 60)
    print(f"  VIDEO {i}/{VIDEOS_PER_RUN}: Running pipeline")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "youtube_agent_system.main", "quick"],
        cwd=WORK_DIR,
        capture_output=False
    )
    
    if result.returncode == 0:
        successes += 1
        print(f"\n  ✅ Video {i} uploaded successfully!")
    else:
        print(f"\n  ❌ Video {i} failed (exit code: {result.returncode})")
    
    # Cleanup generated files between runs
    for f in os.listdir(assets_dir):
        if f.endswith(('.mp4', '.mp3', '.wav')):
            os.remove(os.path.join(assets_dir, f))

print("\n" + "=" * 60)
print(f"  DONE: {successes}/{VIDEOS_PER_RUN} videos uploaded today!")
print("=" * 60)
