# youtube_agent_system/tools/youtube_searcher.py
"""
YouTube Search & Niche Discovery Tool

Uses yt-dlp to search YouTube for:
1. Competitor channels in various niches
2. Educational/advice videos about YouTube growth
3. Trending content patterns

This helps discover what content niches sell best for quick subscriber growth.
"""

import yt_dlp
import re
from typing import Optional
from .. import config


# Queries for finding educational content about YouTube growth
GROWTH_ADVICE_QUERIES = [
    "how to get 10k subscribers fast",
    "youtube shorts monetization tips",
    "AI youtube automation money",
    "reddit story youtube channel growth",
    "how I made money with youtube shorts",
    "youtube shorts algorithm 2024",
    "faceless youtube channel success",
    "story time youtube shorts viral",
]

# Queries for discovering competitor channels by niche
NICHE_DISCOVERY_QUERIES = {
    "AITA": ["reddit aita stories", "am i the asshole youtube", "reddit judgment stories"],
    "REVENGE": ["reddit revenge stories", "pro revenge youtube", "petty revenge stories"],
    "FAMILY_DRAMA": ["reddit family drama", "family secrets revealed story", "toxic family stories"],
    "RELATIONSHIP": ["reddit relationship advice stories", "cheating stories caught", "dating horror stories"],
    "WORKPLACE": ["reddit workplace revenge", "terrible boss stories", "quit my job story"],
    "HORROR": ["reddit scary stories", "true horror stories narration", "creepy reddit stories"],
    "WHOLESOME": ["reddit wholesome stories", "faith in humanity restored", "heartwarming stories"],
}


def search_youtube_videos(query: str, max_results: int = 20) -> list[dict]:
    """
    Searches YouTube for videos matching a query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of dicts with video info (url, title, views, channel, duration)
    """
    print(f"--- [SEARCH] Searching YouTube for: '{query}' ---")
    
    # Build search URL
    search_url = f"ytsearch{max_results}:{query}"
    
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            
            if not info or 'entries' not in info:
                print("  No results found")
                return []
            
            videos = []
            for entry in info['entries']:
                if entry and entry.get('id'):
                    videos.append({
                        'url': f"https://www.youtube.com/watch?v={entry['id']}",
                        'id': entry.get('id', ''),
                        'title': entry.get('title', ''),
                        'channel': entry.get('channel', entry.get('uploader', '')),
                        'channel_url': entry.get('channel_url', entry.get('uploader_url', '')),
                        'views': entry.get('view_count', 0) or 0,
                        'duration': entry.get('duration', 0) or 0,
                    })
            
            print(f"  Found {len(videos)} videos")
            return videos
            
    except Exception as e:
        print(f"  Search error: {e}")
        return []


def search_youtube_shorts(query: str, max_results: int = 20) -> list[dict]:
    """
    Searches specifically for YouTube Shorts (videos under 60 seconds).
    """
    videos = search_youtube_videos(query, max_results * 2)  # Get extra, then filter
    
    # Filter to shorts (under 60 seconds)
    shorts = [v for v in videos if v.get('duration', 0) <= 60 and v.get('duration', 0) > 0]
    
    print(f"  Filtered to {len(shorts)} shorts (≤60s)")
    return shorts[:max_results]


def discover_competitor_channels(niche: str = None) -> list[dict]:
    """
    Discovers competitor YouTube channels in a specific niche.
    
    Args:
        niche: Content niche (AITA, REVENGE, etc.) or None for all niches
        
    Returns:
        List of unique channel dicts with url, name, sample_videos
    """
    print(f"--- [DISCOVER] Finding competitor channels for niche: {niche or 'ALL'} ---")
    
    # Get queries for the niche(s)
    if niche and niche.upper() in NICHE_DISCOVERY_QUERIES:
        queries = NICHE_DISCOVERY_QUERIES[niche.upper()]
    else:
        # Search all niches
        queries = []
        for niche_queries in NICHE_DISCOVERY_QUERIES.values():
            queries.extend(niche_queries[:1])  # Take first query from each
    
    # Search and collect unique channels
    channels = {}
    for query in queries:
        videos = search_youtube_videos(query, max_results=10)
        
        for video in videos:
            channel_url = video.get('channel_url', '')
            if channel_url and channel_url not in channels:
                channels[channel_url] = {
                    'url': channel_url,
                    'name': video.get('channel', 'Unknown'),
                    'sample_videos': [video],
                    'niche_detected': niche or 'MIXED',
                }
            elif channel_url:
                # Add to sample videos
                if len(channels[channel_url]['sample_videos']) < 5:
                    channels[channel_url]['sample_videos'].append(video)
    
    result = list(channels.values())
    print(f"  Discovered {len(result)} unique channels")
    return result


def get_growth_advice_videos(max_per_query: int = 5) -> list[dict]:
    """
    Searches for YouTube videos about channel growth and monetization.
    
    These videos will be analyzed to learn tips and strategies.
    
    Returns:
        List of educational video dicts
    """
    print("--- [ADVICE] Searching for YouTube growth advice videos ---")
    
    all_videos = []
    
    for query in GROWTH_ADVICE_QUERIES:
        videos = search_youtube_videos(query, max_results=max_per_query)
        
        # Prefer videos with high views (likely good advice)
        videos.sort(key=lambda x: x.get('views', 0), reverse=True)
        
        for video in videos[:max_per_query]:
            video['advice_query'] = query
            all_videos.append(video)
    
    # Remove duplicates by video ID
    seen_ids = set()
    unique_videos = []
    for video in all_videos:
        if video['id'] not in seen_ids:
            seen_ids.add(video['id'])
            unique_videos.append(video)
    
    print(f"  Found {len(unique_videos)} unique advice videos")
    return unique_videos


def analyze_niche_potential(niche: str) -> dict:
    """
    Analyzes a content niche's potential based on YouTube search data.
    
    Returns metrics like average views, competition level, etc.
    """
    print(f"--- [ANALYZE] Analyzing niche potential: {niche} ---")
    
    if niche.upper() not in NICHE_DISCOVERY_QUERIES:
        return {'error': f'Unknown niche: {niche}'}
    
    queries = NICHE_DISCOVERY_QUERIES[niche.upper()]
    all_videos = []
    
    for query in queries:
        videos = search_youtube_shorts(query, max_results=20)
        all_videos.extend(videos)
    
    if not all_videos:
        return {
            'niche': niche,
            'potential_score': 0,
            'error': 'No videos found'
        }
    
    # Calculate metrics
    views = [v.get('views', 0) for v in all_videos]
    avg_views = sum(views) / len(views) if views else 0
    max_views = max(views) if views else 0
    
    # Count unique channels (less = less competition)
    unique_channels = len(set(v.get('channel', '') for v in all_videos))
    
    # Calculate potential score (high views + low competition = good)
    # Normalize views to 0-5 scale, competition to 0-5 scale
    view_score = min(avg_views / 100000, 5)  # 500k avg = max score
    competition_score = max(0, 5 - (unique_channels / 4))  # Less channels = higher score
    
    potential_score = (view_score + competition_score) / 2
    
    result = {
        'niche': niche,
        'videos_analyzed': len(all_videos),
        'unique_channels': unique_channels,
        'average_views': int(avg_views),
        'max_views': int(max_views),
        'potential_score': round(potential_score, 2),
        'recommendation': 'HIGH' if potential_score >= 3 else 'MEDIUM' if potential_score >= 1.5 else 'LOW'
    }
    
    print(f"  Niche potential: {result['recommendation']} (score: {result['potential_score']})")
    return result


def discover_all_niche_potentials() -> list[dict]:
    """
    Analyzes all known niches and ranks them by potential.
    
    Returns:
        List of niche analyses sorted by potential score
    """
    print("--- [RANKING] Analyzing all content niches ---")
    
    results = []
    for niche in NICHE_DISCOVERY_QUERIES.keys():
        analysis = analyze_niche_potential(niche)
        if 'error' not in analysis:
            results.append(analysis)
    
    # Sort by potential score
    results.sort(key=lambda x: x.get('potential_score', 0), reverse=True)
    
    print(f"  Top niche: {results[0]['niche'] if results else 'N/A'}")
    return results


def extract_channel_url_from_video(video_url: str) -> Optional[str]:
    """
    Extracts the channel URL from a video URL.
    """
    try:
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('channel_url') or info.get('uploader_url')
            
    except Exception as e:
        print(f"  Error extracting channel: {e}")
        return None


if __name__ == '__main__':
    # Test the searcher
    print("=== Testing YouTube Searcher ===\n")
    
    # Test basic search
    print("1. Basic search test:")
    videos = search_youtube_videos("reddit stories", max_results=5)
    for v in videos[:3]:
        print(f"   - {v['title'][:50]}... ({v['views']} views)")
    
    # Test niche discovery
    print("\n2. Competitor discovery test:")
    channels = discover_competitor_channels("AITA")
    for c in channels[:3]:
        print(f"   - {c['name']}: {c['url']}")
    
    # Test niche analysis
    print("\n3. Niche potential analysis:")
    potentials = discover_all_niche_potentials()
    for p in potentials[:3]:
        print(f"   - {p['niche']}: {p['recommendation']} ({p['potential_score']})")
    
    # Test growth advice
    print("\n4. Growth advice videos:")
    advice = get_growth_advice_videos(max_per_query=2)
    for a in advice[:3]:
        print(f"   - {a['title'][:50]}... ({a['views']} views)")
