#!/bin/bash
# ============================================================
# Oracle Cloud VM Setup Script
# YouTube Agent System - One-Command Setup
# ============================================================
# Usage: bash setup_cloud.sh
# Tested on: Ubuntu 22.04 (Oracle Cloud ARM/AMD)
# ============================================================

set -e  # Exit on any error

echo "============================================================"
echo "  YouTube Agent System - Cloud Setup"
echo "============================================================"

# --- System Updates ---
echo "[1/7] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# --- Install Python 3.11+ ---
echo "[2/7] Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# --- Install ffmpeg (required for video rendering) ---
echo "[3/7] Installing ffmpeg..."
sudo apt install -y ffmpeg

# --- Install other system dependencies ---
echo "[4/7] Installing system dependencies..."
sudo apt install -y \
    git \
    imagemagick \
    libmagic1 \
    fonts-montserrat \
    build-essential

# Fix ImageMagick policy for MoviePy
sudo sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml 2>/dev/null || true

# --- Clone/update the project ---
echo "[5/7] Setting up project..."
PROJECT_DIR="$HOME/youtube_agent_system"

if [ -d "$PROJECT_DIR" ]; then
    echo "  Project directory exists, pulling latest..."
    cd "$PROJECT_DIR"
    git pull 2>/dev/null || echo "  Not a git repo, skipping pull"
else
    echo "  Creating project directory..."
    mkdir -p "$PROJECT_DIR"
    echo "  >> Copy your project files to: $PROJECT_DIR"
fi

# --- Create virtual environment and install Python dependencies ---
echo "[6/7] Setting up Python environment..."
cd "$PROJECT_DIR"

python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install \
    groq \
    edge-tts \
    moviepy \
    whisper-timestamped \
    chromadb \
    python-dotenv \
    google-auth \
    google-auth-oauthlib \
    google-api-python-client \
    datasets \
    yt-dlp \
    praw \
    requests \
    Pillow

# --- Create required directories ---
echo "[7/7] Creating directories..."
mkdir -p youtube_agent_system/generated_assets
mkdir -p youtube_agent_system/logs
mkdir -p youtube_agent_system/fonts
mkdir -p youtube_agent_system/chroma_db

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo ""
echo "  Next steps:"
echo "  1. Copy your .env file:  scp .env user@vm:~/youtube_agent_system/youtube_agent_system/.env"
echo "  2. Copy client_secrets:  scp client_secrets.json user@vm:~/youtube_agent_system/"
echo "  3. Copy OAuth token:     scp token.pickle user@vm:~/youtube_agent_system/"
echo "  4. Copy fonts:           scp fonts/* user@vm:~/youtube_agent_system/youtube_agent_system/fonts/"
echo "  5. Copy background video to the project directory"
echo "  6. Install the systemd service:"
echo "     sudo cp deploy/youtube_agent.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable youtube_agent"
echo "     sudo systemctl start youtube_agent"
echo ""
echo "  To run manually:"
echo "     source venv/bin/activate"
echo "     python -m youtube_agent_system.smart_scheduler"
echo ""
