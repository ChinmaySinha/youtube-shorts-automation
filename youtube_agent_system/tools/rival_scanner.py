import yt_dlp

def get_video_title(url: str) -> str | None:
    """
    (Legacy) Extracts the title of a single YouTube video from its URL.
    """
    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', None)
    except Exception as e:
        print(f"Error scanning single URL '{url}': {e}")
        return None

def get_channel_shorts_info(channel_url: str, playlist_end: int = 5) -> list[dict] | None:
    """
    Scrapes a YouTube channel for recent video titles and view counts.
    It first tries the /shorts feed, and if that fails, it falls back to the /videos feed.

    Args:
        channel_url: The URL of the YouTube channel.
        playlist_end: The number of recent videos to scrape (default 5).

    Returns:
        A list of dictionaries, each containing 'title' and 'views', or None on error.
    """
    # URLs to attempt, in order of preference
    channel_feeds = [
        channel_url.rstrip('/') + '/shorts',
        channel_url.rstrip('/') + '/videos'
    ]

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'playlistend': playlist_end,
        'skip_download': True,
    }

    for feed_url in channel_feeds:
        print(f"--- Scanning rival channel feed: {feed_url} ---")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_dict = ydl.extract_info(feed_url, download=False)

                video_infos = []
                if 'entries' in playlist_dict and playlist_dict['entries']:
                    for video in playlist_dict['entries']:
                        # A second call is needed to get the view_count
                        video_details = ydl.extract_info(video['url'], download=False)
                        title = video_details.get('title')
                        view_count = video_details.get('view_count')

                        if title and view_count is not None:
                            video_infos.append({'title': title, 'views': view_count})
                            print(f"Found rival video: '{title}' ({view_count} views)")
                    
                    video_infos.sort(key=lambda x: x['views'], reverse=True)
                    return video_infos
                else:
                    print(f"Could not find any videos for feed: {feed_url}")
        
        except yt_dlp.utils.DownloadError as e:
            if "This channel does not have a shorts tab" in str(e):
                print(f"Channel does not have a shorts tab. Trying the main videos feed...")
                continue
            else:
                print(f"An unexpected download error occurred while scanning '{feed_url}': {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred while scanning '{feed_url}': {e}")
            return None

    print(f"Could not retrieve videos from any feed for channel: {channel_url}")
    return None

if __name__ == '__main__':
    test_channel_1 = "https://www.youtube.com/@Broken.Stories"
    videos_1 = get_channel_shorts_info(test_channel_1, playlist_end=5)
    if videos_1:
        print("\n--- Successfully extracted from channel 1 ---")
        for video in videos_1:
            print(f"Title: {video['title']}, Views: {video['views']}")

    test_channel_2 = "https://www.youtube.com/@MrBeast"
    videos_2 = get_channel_shorts_info(test_channel_2, playlist_end=5)
    if videos_2:
        print("\n--- Successfully extracted from channel 2 ---")
        for video in videos_2:
            print(f"Title: {video['title']}, Views: {video['views']}")