# Autonomous Agentic YouTube Content System

This project is a fully autonomous system for generating and publishing YouTube content, built based on the provided agentic design blueprint. This README provides all the necessary instructions to set up and run the system.

## Table of Contents
1.  [Project Structure](#project-structure)
2.  [Setup Instructions](#setup-instructions)
    - [Step 1: Install Dependencies](#step-1-install-dependencies)
    - [Step 2: Set Up API Keys](#step-2-set-up-api-keys)
3.  [How to Run the System](#how-to-run-the-system)
4.  [How to Test Individual Components](#how-to-test-individual-components)
5.  [Future Development](#future-development)

## Project Structure

The project is organized into a modular, agent-based architecture:

```
/
|-- requirements.txt            # All Python dependencies
|-- README.md                   # This file
|-- youtube_agent_system/
|   |-- .env_example            # Template for environment variables
|   |-- config.py               # Loads configuration and API keys
|   |-- main.py                 # Main entry point to run the MVP pipeline
|   |-- content_agent.py        # Generates the video script
|   |-- production_agent.py     # Creates the final video file
|   |-- publishing_agent.py     # Publishes the video to YouTube
|   |-- supervisor_agent.py     # (Future) Advanced orchestrator
|   |-- strategy_agent.py       # (Future) Decides what content to create
|   |-- analytics_agent.py      # (Future) Analyzes video performance
|   |-- knowledge_base.py       # (Future) Manages long-term memory
|   |-- tools/                  # Directory for helper modules
|   |   |-- audio_tools.py      # Handles Text-to-Speech
|   |   |-- video_tools.py      # Handles fetching stock video
|   |   |-- editing_tools.py    # Handles video composition with MoviePy
|   |   |-- youtube_tools.py    # Handles YouTube API interaction
```

## Setup Instructions

### Step 1: Install Dependencies

Ensure you have Python 3 installed. Then, open your terminal and navigate to the root directory of this project (the one containing `requirements.txt`) and run:

```bash
pip install -r requirements.txt
```

### Step 2: Set Up API Keys

This project requires credentials for three external services.

#### Part A: Create the `.env` file

1.  Navigate into the `youtube_agent_system` directory.
2.  Find the file named `.env_example` and **rename it to `.env`**.
3.  Open the `.env` file. You will fill in the values in the next parts.

#### Part B: Get Groq API Key (for AI Model)

1.  Go to [https://console.groq.com/](https://console.groq.com/) and sign up for a free account.
2.  Click on **"API Keys"** in the left-hand menu.
3.  Create a new API key, copy it, and paste it into your `.env` file for the `GROQ_API_KEY` variable.

#### Part C: Get Pexels API Key (for Background Videos)

1.  Go to [https://www.pexels.com/api/](https://www.pexels.com/api/) and sign up.
2.  They will provide you with your API key.
3.  Copy the key and paste it into your `.env` file for the `PEXELS_API_KEY` variable.

#### Part D: Get YouTube API Credentials (for Uploading)

This is the most complex part. You need to create a special `client_secrets.json` file.

1.  **Go to Google Cloud Console:** [https://console.cloud.google.com/](https://console.cloud.google.com/)
2.  **Create a Project:** Create a new project if you don't have one.
3.  **Enable the API:** Search for **"YouTube Data API v3"** and **Enable** it for your project.
4.  **Configure the OAuth Consent Screen:**
    *   In the left menu, go to **"APIs & Services" -> "OAuth consent screen"**.
    *   Select **"External"** and click **"Create"**.
    *   Provide an app name (e.g., "YouTube Agent"), a user support email, and developer contact info.
    *   Click **"Save and Continue"** until you get to the **"Test users"** screen.
    *   **Crucial Step:** Click **"+ Add Users"** and add the Google account email you will use to upload videos.
    *   Click **"Save and Continue"** and then **"Back to Dashboard"**.
5.  **Create the Credentials:**
    *   In the left menu, go to **"APIs & Services" -> "Credentials"**.
    *   Click **"+ Create Credentials"** -> **"OAuth client ID"**.
    *   For "Application type", choose **"Desktop app"**.
    *   Click **"Create"**.
6.  **Download and Place the File:**
    *   A window will pop up. Click **"Download JSON"**.
    *   The file will have a long name. **You must rename this file to `client_secrets.json`**.
    *   **You must place this `client_secrets.json` file inside the `youtube_agent_system` directory**.

## How to Run the System

Once all setup is complete:

1.  Open your terminal.
2.  Navigate to the **root directory** of the project (the one containing the `youtube_agent_system` folder).
3.  Run the following command:

    ```bash
    python -m youtube_agent_system.main --topic "a story about a library at the bottom of the ocean"
    ```
4.  You can change the topic in the command to anything you like.
5.  **First Run Only:** Your web browser will open and ask you to log in to your Google account and approve the permissions for the app you created. This is expected and necessary for the script to upload videos for you.

## How to Test Individual Components

You can test parts of the system in isolation by running the individual files as scripts. For example, to test only the content generation:

```bash
python -m youtube_agent_system.content_agent
```

## Future Development

The files `supervisor_agent.py`, `strategy_agent.py`, `analytics_agent.py`, and `knowledge_base.py` are placeholders for the advanced Phase 2 and 3 features described in your blueprint. You can now build out the logic in these files to make the system fully autonomous and self-improving.
