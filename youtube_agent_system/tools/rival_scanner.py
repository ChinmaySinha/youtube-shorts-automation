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

def get_channel_shorts_info(channel_url: str, playlist_end: int = 10) -> list[dict] | None:
    """
    Scrapes the /shorts feed of a YouTube channel for video titles and view counts.

    Args:
        channel_url: The URL of the YouTube channel.
        playlist_end: The number of recent shorts to scrape (default 10).

    Returns:
        A list of dictionaries, each containing 'title' and 'views',
        or None if an error occurs.
    """
    # Ensure the URL points to the shorts feed for yt-dlp
    if not channel_url.endswith('/shorts'):
        channel_url = channel_url.rstrip('/') + '/shorts'

    print(f"--- Scanning rival channel: {channel_url} ---")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist', # Don't extract full info for each video, just the list
        'playlistend': playlist_end,   # Limit to the N most recent shorts
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # This gets a flat list of video entries in the playlist (the /shorts feed)
            playlist_dict = ydl.extract_info(channel_url, download=False)

            video_infos = []
            if 'entries' in playlist_dict:
                for video in playlist_dict['entries']:
                    # Now we need to get the view count for each video, which requires a second call
                    # This is inefficient but necessary as view_count isn't in the flat extract
                    video_details = ydl.extract_info(video['url'], download=False)
                    title = video_details.get('title')
                    view_count = video_details.get('view_count')

                    if title and view_count is not None:
                        video_infos.append({'title': title, 'views': view_count})
                        print(f"Found rival short: '{title}' ({view_count} views)")

                # Sort by view count descending to find the most popular ones
                video_infos.sort(key=lambda x: x['views'], reverse=True)
                return video_infos
            else:
                print(f"Could not find any videos for channel: {channel_url}")
                return None

    except Exception as e:
        print(f"An error occurred while scanning channel '{channel_url}': {e}")
        return None

if __name__ == '__main__':
    # Example usage:
    test_channel_url = "https://www.youtube.com/@Broken.Stories"
    videos = get_channel_shorts_info(test_channel_url, playlist_end=5) # Scan last 5 shorts

    if videos:
        print("\n--- Successfully extracted video info ---")
        for video in videos:
            print(f"Title: {video['title']}, Views: {video['views']}")
    else:
        print("\n--- Failed to extract video info ---")
