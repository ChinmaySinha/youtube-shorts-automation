# youtube_agent_system/tools/rival_scanner.py
import yt_dlp

def get_channel_shorts_info(channel_url: str, playlist_end: int = 5) -> list[dict] | None:
    """
    Scans a YouTube channel for Shorts and returns their titles and view counts.
    """
    if "/shorts" not in channel_url:
        shorts_url = f"{channel_url}/shorts"
    else:
        shorts_url = channel_url

    # --- UPDATED: More flexible ydl_opts ---
    ydl_opts = {
        'playlistend': playlist_end,
        'extract_flat': True,
        'quiet': True,
        'force_generic_extractor': True,
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]', # More flexible format selection
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(shorts_url, download=False)
            
            if 'entries' in info and info['entries']:
                videos_info = []
                for entry in info['entries']:
                    if entry:
                        videos_info.append({
                            'title': entry.get('title'),
                            'views': entry.get('view_count'),
                        })
                return videos_info
            else:
                return None # No shorts found or channel structure is different

    except yt_dlp.utils.DownloadError as e:
        # This error often means the /shorts tab doesn't exist
        if "channel does not have a shorts tab" in str(e):
            print("Channel does not have a shorts tab. Trying the main videos feed...")
            return _get_videos_from_main_feed(channel_url, playlist_end)
        else:
            print(f"An unexpected download error occurred while scanning '{channel_url}': {e}")
            return None
    except Exception as e:
        print(f"An unexpected error occurred while scanning '{channel_url}': {e}")
        return None

def _get_videos_from_main_feed(channel_url: str, playlist_end: int = 5) -> list[dict] | None:
    """
    Fallback function to get videos from the main /videos feed if /shorts fails.
    """
    videos_url = f"{channel_url}/videos"
    
    # --- UPDATED: More flexible ydl_opts for fallback ---
    ydl_opts = {
        'playlistend': playlist_end,
        'extract_flat': True,
        'quiet': True,
        'force_generic_extractor': True,
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(videos_url, download=False)
            
            if 'entries' in info and info['entries']:
                videos_info = []
                for entry in info['entries']:
                    if entry:
                        print(f"Found rival video: '{entry.get('title')}' ({entry.get('view_count')} views)")
                        videos_info.append({
                            'title': entry.get('title'),
                            'views': entry.get('view_count'),
                        })
                return videos_info
            return None
    except Exception as e:
        print(f"An unexpected download error occurred while scanning '{videos_url}': {e}")
        return None