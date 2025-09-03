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
YOUTUBE_CLIENT_SECRETS_FILE = "client_secrets.json"
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "generated_assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure the directories exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "fonts"), exist_ok=True)


# --- Content & Production Settings ---

STATIC_TOPIC_POOL = [
    "AITA for exposing my cheating girlfriend to her family at her own birthday party?",
    "My sister stole my inheritance, so I got pro revenge by ruining her wedding.",
    "AITA for refusing to give up my first-class seat for a celebrity's child?",
    "My roommate ate my expensive food, so I replaced it with the world's spiciest ghost pepper extract.",
    "AITA for telling my parents I won't pay for my brother's college after they spent my tuition fund on a vacation?",
    "My landlord tried to illegally evict me, so I used the law to make his life a living nightmare.",
    "AITA for reporting my friend's 'emotional support' dog after it destroyed my apartment?",
    "My entitled cousin demanded my wedding dress, so I gave her a cheap knockoff and watched the chaos unfold.",
]

# --- CORRECTED LIST OF RIVAL CHANNELS ---
RIVAL_CHANNEL_URLS = [
    "https://www.youtube.com/@RedditJar",
    "https://www.youtube.com/@redditdramatale",
    "https://www.youtube.com/@Broken.Stories",
]

DEFAULT_TOPIC = "the story of a forgotten house-keeper who had the biggest glow-up"

GAMEPLAY_QUERIES = [
    "minecraft parkour",
    "gta v gameplay",
    "satisfying compilation",
]

LOCAL_VIDEO_FALLBACK_PATH = r"youtube_agent_system\Minecraft Parkour Gameplay NO COPYRIGHT (Vertical) - Orbital - No Copyright Gameplay (1080p, h264).mp4"

# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_SPEED = 1.4

# Text overlay settings
TEXT_COLOR = "#1FABAB" 
TEXT_FONT = "Montserrat-Black.ttf"
TEXT_FONT_SIZE = 84
TEXT_STROKE_COLOR = "black"
TEXT_STROKE_WIDTH = 8
TEXT_POSITION = ("center", "center")

# Voiceover settings
VOICEOVER_LANGUAGE = "en"
VOICEOVER_Tld = "co.uk"