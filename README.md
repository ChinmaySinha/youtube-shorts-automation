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
|   |-- main.py                 # Main entry point to run the pipeline
|   |-- content_agent.py        # Generates the video script
|   |-- production_agent.py     # Creates the final video file
|   |-- publishing_agent.py     # Publishes the video to YouTube
|   |-- supervisor_agent.py     # (Future) Advanced orchestrator
|   |-- strategy_agent.py       # Decides what content to create
|   |-- analytics_agent.py      # Analyzes video performance
|   |-- knowledge_base.py       # Manages long-term memory
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
*Note: If you encounter module errors, especially with `moviepy`, run this command again with the `--no-cache-dir` and `--upgrade` flags to ensure you get fresh, complete copies of the libraries: `pip install --upgrade --no-cache-dir -r requirements.txt`*

### Step 2: Set Up API Keys

This project requires credentials for three external services.

#### Part A: Create the `.env` file

1.  Navigate into the `youtube_agent_system` directory.
2.  Find the file named `.env_example` and **rename it to `.env`**.
3.  Open the `.env` file. You will fill in the values in the next parts.

#### Part B: Get Groq API Key (for AI Model)

1.  Go to [https://console.groq.com/](https://console.groq.com/) and sign up for a free account.
2.  Click on **"API Keys"** in the left-hand menu.
3.  Create a new API key and paste it into your `.env` file for the `GROQ_API_KEY` variable.

#### Part C: Get Pexels API Key (for Background Videos)

1.  Go to [https://www.pexels.com/api/](https://www.pexels.com/api/) and sign up.
2.  They will provide you with your API key.
3.  Copy the key and paste it into your `.env` file for the `PEXELS_API_KEY` variable.

#### Part D: Get YouTube API Credentials (for Uploading & Analytics)

This is the most complex part. You need to create a special `client_secrets.json` file.

1.  **Go to Google Cloud Console:** [https://console.cloud.google.com/](https://console.cloud.google.com/)
2.  **Create a Project:** Create a new project if you don't have one.
3.  **Enable the APIs:** Search for and **Enable** both of these APIs for your project:
    *   **YouTube Data API v3**
    *   **YouTube Analytics API**
4.  **Configure the OAuth Consent Screen:**
    *   Go to **"APIs & Services" -> "OAuth consent screen"**.
    *   Select **"External"** and click **"Create"**.
    *   Provide an app name, user support email, and developer contact info.
    *   **Crucial Step:** On the "Test users" screen, click **"+ Add Users"** and add the Google account email you will use to upload videos.
    *   Save and continue until you are back at the dashboard.
5.  **Create the Credentials:**
    *   Go to **"APIs & Services" -> "Credentials"**.
    *   Click **"+ Create Credentials"** -> **"OAuth client ID"**.
    *   For "Application type", choose **"Desktop app"**.
    *   Click **"Create"** and then **"Download JSON"**.
6.  **Download and Place the File:**
    *   Rename the downloaded file to **`client_secrets.json`**.
    *   Place this file inside the **`youtube_agent_system`** directory.

## How to Run the System

The system is now fully autonomous. It no longer requires a topic to be provided manually.

1.  Open your terminal.
2.  Navigate to the **root directory** of the project (the one containing the `youtube_agent_system` folder).
3.  Run the following command:

    ```bash
    python -m youtube_agent_system.main
    ```
4.  The script will now run the full learning loop: analyze a past video (if any), decide on a new topic, create the video, and publish it.
5.  **First Run Only:** Your web browser will open and ask you to log in and approve the new permissions (including YouTube Analytics). This is expected.

## How to Test Individual Components

You can still test parts of the system in isolation by running the individual files as scripts. For example, to test only the content generation:

```bash
python -m youtube_agent_system.content_agent
```

## Future Development

This project is now a learning agent. The next steps involve refining the learning algorithms, potentially adding more data sources for the `StrategyAgent`, and implementing A/B testing based on the groundwork laid in the `PublishingAgent`.
