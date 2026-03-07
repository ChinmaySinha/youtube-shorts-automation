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

# Gemini API for Video Content Analysis (Learning from rivals)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

# --- Learning Configuration ---
RIVAL_SCAN_VIDEOS_PER_CHANNEL = 15  # How many videos to analyze per rival channel
PATTERN_UPDATE_FREQUENCY = 10      # Update patterns every N videos
MIN_SAMPLES_FOR_PATTERN = 3        # Minimum videos to form a pattern

# Performance thresholds for content decisions
LOW_PERFORMANCE_THRESHOLD = 0.3   # Below this = try new approach
HIGH_PERFORMANCE_THRESHOLD = 0.7  # Above this = keep the pattern

# --- Reddit API Configuration (Optional) ---
# Create app at: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "youtube_content_bot/1.0 (by content_researcher)"

# Story subreddits to scrape for content
STORY_SUBREDDITS = [
    "AmItheAsshole", "ProRevenge", "pettyrevenge",
    "MaliciousCompliance", "relationship_advice", "tifu",
    "entitledparents", "ChoosingBeggars", "confession"
]

# --- Autonomous Runner Configuration ---
CHECKPOINT_INTERVAL_MINUTES = 30   # How often to save progress
MAX_RUNTIME_HOURS = 24             # Default max runtime
VIDEOS_PER_CYCLE = 1               # Videos to produce per research cycle
CYCLE_DELAY_MINUTES = 5            # Delay between production cycles
EXTENDED_VIDEOS_PER_CHANNEL = 50   # Extended rival analysis limit


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

EDGE_TTS_VOICE = "en-US-GuyNeural"  # Deep, natural male voice

# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_SPEED = 1.5

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

# ============================================================
# YouTube Shorts Algorithm Optimization Settings
# ============================================================
# Based on analysis of 35B+ Shorts views:
# - Optimal lengths: 13 seconds (quick hit) or 60 seconds (full story)
# - First 3 seconds are CRITICAL for retention (seed audience test)
# - Algorithm uses Explore (seed) -> Exploit (broad push) phases
# - Metadata (title, description, hashtags, spoken words) = categorization
# - Engaged Views (not raw views) drive YPP eligibility and revenue

# Target video durations (seconds) — algorithm sweet spots
SHORTS_TARGET_DURATION_SHORT = 13   # Quick, punchy stories
SHORTS_TARGET_DURATION_LONG = 60    # Full dramatic stories (our primary target)

# Word count targets calibrated to voiceover speed (~2.5 words/sec at 1.4x speed)
# For a 50-60 second Short at normal narration pace
SHORTS_MIN_WORDS = 200
SHORTS_MAX_WORDS = 300
SHORTS_IDEAL_WORDS = 250  # ~60 seconds of narration

# First 3 seconds: the hook window that determines seed audience retention
SHORTS_HOOK_DURATION_SECONDS = 3
SHORTS_HOOK_MAX_WORDS = 15  # ~3 seconds worth of spoken hook

# Shorts-specific hashtags for algorithm categorization
SHORTS_DEFAULT_HASHTAGS = [
    "#shorts", "#storytime", "#reddit", "#aita",
    "#redditstories", "#viral", "#fyp"
]

# Category-specific hashtags to boost algorithm matching
SHORTS_CATEGORY_HASHTAGS = {
    "AITA": ["#aita", "#amItheasshole", "#redditaita", "#storytime"],
    "REVENGE": ["#revenge", "#prorevenge", "#pettyrevenge", "#karma", "#justiceserved"],
    "FAMILY_DRAMA": ["#familydrama", "#toxicfamily", "#narcissisticparents", "#inlaws"],
    "RELATIONSHIP": ["#relationship", "#dating", "#breakup", "#cheating"],
    "CONFESSION": ["#confession", "#trueoffmychest", "#secrets", "#confessions"],
    "ENTITLED": ["#entitled", "#entitledparents", "#karen", "#karenmeltdown"],
    "STORIES": ["#tifu", "#redditstories", "#storytime", "#truestory"],
}

# ============================================================
# Algorithm Signal: Upload Frequency & Consistency
# ============================================================
# Consistency is rewarded by the algorithm. Channels that post regularly
# get prioritized in the feed. Minimum: weekly. Ideal: 3-5x per week.
SHORTS_MIN_UPLOADS_PER_WEEK = 3
SHORTS_IDEAL_UPLOADS_PER_WEEK = 5

# ============================================================
# Algorithm Signal: Viewer Interaction (Comments, Shares, Remixes)
# ============================================================
# The algorithm now considers comments, shares, and remixes as ranking signals.
# Encouraging viewers to interact boosts algorithmic placement.
# These CTA templates are appended to video descriptions.
SHORTS_ENGAGEMENT_CTA_TEMPLATES = [
    "What would YOU have done? Drop your answer below!",
    "Was this the right move? Comment your verdict!",
    "Who was the real villain here? Tell me in the comments!",
    "Would you have stayed or walked away? Let me know!",
    "Share this with someone who needs to hear this story!",
    "Tag a friend who's been through something like this!",
    "Like if you think they made the right call!",
    "Part 2? Comment YES if you want to hear what happened next!",
]

# ============================================================
# Algorithm Signal: Cross-Platform Sharing
# ============================================================
# Algorithm favors content shared across TikTok, Reels, and Facebook.
# This flag enables cross-platform metadata optimization.
SHORTS_CROSS_PLATFORM_ENABLED = True
SHORTS_CROSS_PLATFORM_TAGS = ["#tiktok", "#reels", "#viral", "#trending"]

# ============================================================
# Algorithm Signal: Satisfaction > Watch Time
# ============================================================
# YouTube runs satisfaction surveys. Content with long-term rewatchability
# and emotional satisfaction scores higher than raw watch time alone.
# Scripts should aim for "rewatchable" endings (twists, callbacks).
SHORTS_SATISFACTION_PRIORITY = True  # Optimize for satisfaction over raw views

# As of 2025, Shorts can be up to 3 minutes (180 seconds)
# We still target 60s as the sweet spot, but support extended format
SHORTS_MAX_DURATION = 180  # 3 minutes max
SHORTS_EXTENDED_WORDS = 600  # For 2-3 minute Shorts if needed