import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- API Keys and Configuration ---

# Groq API for Language Model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Pexels API for Stock Videos
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# ElevenLabs API for High-Quality TTS
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# YouTube Data API v3
# The client secrets file is needed for OAuth 2.0
YOUTUBE_CLIENT_SECRETS_FILE = "client_secrets.json"
# The scopes define the permissions the app will request
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YT_ANALYTICS_API_SERVICE_NAME = "youtubeAnalytics"
YT_ANALYTICS_API_VERSION = "v2"


# --- Project Structure & File Paths ---
# This helps in managing file paths consistently across modules

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for storing generated content (videos, audio, etc.)
ASSETS_DIR = os.path.join(BASE_DIR, "generated_assets")

# Ensure the assets directory exists
os.makedirs(ASSETS_DIR, exist_ok=True)


# --- Content & Production Settings ---

# List of predefined Reddit-style story topics.
# The system will use these when it cannot find new topics from rivals.
STATIC_TOPIC_POOL = [
    "AITA for exposing my cheating ex-girlfriend to her entire family at her wedding?",
    "My entitled boss stole my work and took credit, so I got pro revenge by deleting the master files.",
    "AITA for refusing to give up my first-class seat for a newlywed couple on their honeymoon?",
    "My roommate kept eating my food, so I made the spiciest chili in the world as revenge.",
    "AITA for telling my parents I won't pay for my sister's college after they spent my tuition fund?",
]

# List of rival YouTube channel URLs to scan for new topic ideas.
# More can be added here.
RIVAL_CHANNEL_URLS = [
    "https://www.youtube.com/@Broken.Stories",
]

# Default topic if none is provided (fallback)
DEFAULT_TOPIC = "the story of a forgotten lighthouse keeper"

# Search queries for background gameplay footage.
# The system will randomly pick one of these for each video.
GAMEPLAY_QUERIES = [
    "minecraft parkour",
    "gta v gameplay",
    "satisfying compilation",
    "racing simulator",
]

# Path to a local video file to use as a fallback if Pexels API fails.
# Leave as an empty string "" to not use a fallback.
# Example: r"C:\Users\YourUser\Videos\my_gameplay.mp4"
LOCAL_VIDEO_FALLBACK_PATH = ""

# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920 # 9:16 aspect ratio for shorts
VIDEO_FPS = 24

# Text overlay settings
TEXT_COLOR = "white"
TEXT_FONT = r"C:\Windows\Fonts\arialbd.ttf" # A common font, might need to change based on system
TEXT_FONT_SIZE = 70
TEXT_STROKE_COLOR = "black"
TEXT_STROKE_WIDTH = 2
TEXT_POSITION = ("center", "center")

# Voiceover settings
VOICEOVER_LANGUAGE = "en"
VOICEOVER_Tld = "co.uk" # Top-level domain for accent, e.g., 'co.uk', 'com.au'