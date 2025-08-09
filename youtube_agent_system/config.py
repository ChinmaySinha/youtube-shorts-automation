import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- API Keys and Configuration ---

# Groq API for Language Model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Pexels API for Stock Videos
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# YouTube Data API v3
# The client secrets file is needed for OAuth 2.0
YOUTUBE_CLIENT_SECRETS_FILE = "client_secrets.json"
# The scopes define the permissions the app will request
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


# --- Project Structure & File Paths ---
# This helps in managing file paths consistently across modules

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for storing generated content (videos, audio, etc.)
ASSETS_DIR = os.path.join(BASE_DIR, "generated_assets")

# Ensure the assets directory exists
os.makedirs(ASSETS_DIR, exist_ok=True)


# --- Content & Production Settings ---

# Default topic if none is provided
DEFAULT_TOPIC = "the story of a forgotten lighthouse keeper"

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
