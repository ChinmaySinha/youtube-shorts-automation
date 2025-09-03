import os
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .. import config

def _get_credentials():
    """Handles the OAuth 2.0 flow and returns valid credentials."""
    creds = None
    token_path = os.path.join(config.BASE_DIR, 'token.pickle')

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secrets_file = os.path.join(config.BASE_DIR, config.YOUTUBE_CLIENT_SECRETS_FILE)
            if not os.path.exists(secrets_file):
                print("!!! ERROR: client_secrets.json not found. !!!")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, config.YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_youtube_service():
    """Builds and returns the YouTube Data API service object."""
    credentials = _get_credentials()
    if not credentials:
        return None
    return build(config.YOUTUBE_API_SERVICE_NAME, config.YOUTUBE_API_VERSION, credentials=credentials)

def upload_video_to_youtube(video_path: str, title: str, description: str, tags: list[str]) -> str | None:
    """Uploads a video to YouTube and returns the new video's ID."""
    try:
        youtube = get_youtube_service()
        if not youtube:
            print("Could not get YouTube service. Aborting upload.")
            return None

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22"
            },
            "status": { "privacyStatus": "public" }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        print(f"--- Uploading video '{title}' to YouTube ---")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        video_id = response.get('id')
        print(f"--- Upload Successful! Video ID: {video_id} ---")
        return video_id

    except Exception as e:
        print(f"An error occurred during YouTube upload: {e}")
        return None

def get_video_analytics(video_id: str) -> dict | None:
    """Fetches key performance indicators for a specific YouTube video."""
    print(f"--- Fetching analytics for video ID: {video_id} ---")
    try:
        credentials = _get_credentials()
        if not credentials:
            print("Could not get credentials. Aborting analytics fetch.")
            return None

        analytics = build(
            config.YT_ANALYTICS_API_SERVICE_NAME,
            config.YT_ANALYTICS_API_VERSION,
            credentials=credentials
        )

        today = datetime.utcnow().date()
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

        request = analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,averageViewDuration',
            dimensions='video',
            filters=f'video=={video_id}'
        )
        response = request.execute()

        if response and 'rows' in response and response['rows']:
            stats = response['rows'][0]
            analytics_data = {
                'views': stats[1],
                'likes': stats[2],
                'average_view_duration': stats[3]
            }
            print(f"Analytics found: {analytics_data}")
            return analytics_data
        else:
            print("No analytics data found for this video yet.")
            return None

    except Exception as e:
        print(f"An error occurred during YouTube analytics fetch: {e}")
        return None