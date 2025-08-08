import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .. import config

# This file handles the complexities of YouTube API authentication and uploading.
#
# IMPORTANT USER ACTION REQUIRED:
# 1. Go to the Google Cloud Console (https://console.cloud.google.com/).
# 2. Create a new project.
# 3. Enable the "YouTube Data API v3".
# 4. Create credentials for an "OAuth 2.0 Client ID".
# 5. Select "Desktop app" as the application type.
# 6. Download the JSON file. Rename it to "client_secrets.json" and
#    place it in the "youtube_agent_system" directory, next to your main.py.
#
# This process is essential for the upload functionality to work.

def get_youtube_service():
    """
    Authenticates with the YouTube API and returns a service object.
    Handles token storage and refresh.
    """
    creds = None
    token_path = os.path.join(config.BASE_DIR, 'token.pickle')

    # Load credentials from token file if it exists
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secrets_file = os.path.join(config.BASE_DIR, config.YOUTUBE_CLIENT_SECRETS_FILE)
            if not os.path.exists(secrets_file):
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print("!!! ERROR: client_secrets.json not found.            !!!")
                print("!!! Please follow the setup instructions in          !!!")
                print("!!! youtube_agent_system/tools/youtube_tools.py      !!!")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, config.YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build(config.YOUTUBE_API_SERVICE_NAME, config.YOUTUBE_API_VERSION, credentials=creds)

def upload_video_to_youtube(video_path: str, title: str, description: str, tags: list[str]):
    """
    Uploads a video to YouTube with the given metadata.
    """
    try:
        youtube = get_youtube_service()
        if not youtube:
            print("Could not get YouTube service. Aborting upload.")
            return

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22" # "People & Blogs". Change if needed. See https://developers.google.com/youtube/v3/docs/videoCategories/list
            },
            "status": {
                "privacyStatus": "private" # 'private', 'public', or 'unlisted'
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        print(f"--- Uploading video '{title}' to YouTube ---")
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        print(f"--- Upload Successful! ---")
        print(f"Video ID: {response.get('id')}")
        print(f"Watch on YouTube: https://www.youtube.com/watch?v={response.get('id')}")

    except Exception as e:
        print(f"An error occurred during YouTube upload: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # A simple test to check authentication.
    # This will trigger the OAuth flow if it's the first time.
    print("Checking YouTube authentication...")
    service = get_youtube_service()
    if service:
        print("Successfully authenticated with YouTube.")
    else:
        print("Failed to authenticate with YouTube.")
