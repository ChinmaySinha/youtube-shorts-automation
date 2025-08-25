import yt_dlp

def get_video_title(url: str) -> str | None:
    """
    Extracts the title of a YouTube video from its URL.

    Args:
        url: The full URL of the YouTube video.

    Returns:
        The title of the video as a string, or None if an error occurs.
    """
    ydl_opts = {
        'quiet': True,       # Suppress console output
        'no_warnings': True, # Suppress warnings
        'skip_download': True, # Do not download the video
        'force_generic_extractor': True, # Essential for getting info without a full parse
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', None)
            if title:
                print(f"Scanned rival video. Title: '{title}'")
                return title
            else:
                print(f"Could not extract title from URL: {url}")
                return None
    except yt_dlp.utils.DownloadError as e:
        # This can happen for private videos, deleted videos, or invalid URLs
        print(f"Error scanning URL '{url}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while scanning URL '{url}': {e}")
        return None

if __name__ == '__main__':
    # Example usage:
    test_url = "https://www.youtube.com/watch?v=s600FYgI5-s" # URL provided by user
    title = get_video_title(test_url)
    if title:
        print(f"\nSuccessfully extracted title: {title}")
    else:
        print("\nFailed to extract title.")

    # Example of a failing URL
    test_fail_url = "https://www.youtube.com/watch?v=invalidurl123"
    title_fail = get_video_title(test_fail_url)
    if not title_fail:
        print("\nCorrectly handled failing URL.")
