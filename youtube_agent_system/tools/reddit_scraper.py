# youtube_agent_system/tools/reddit_scraper.py
"""
Reddit Story Scraper

Collects viral stories from Reddit for content inspiration.
Uses PRAW (Python Reddit API Wrapper) if credentials are available,
otherwise falls back to web scraping.

Subreddits targeted:
- r/AmItheAsshole (AITA)
- r/ProRevenge, r/pettyrevenge, r/MaliciousCompliance
- r/relationship_advice, r/tifu
- r/entitledparents, r/ChoosingBeggars
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional

# Try to import PRAW, but don't fail if not installed
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("Warning: PRAW not installed. Reddit scraping will be limited.")

from .. import config


# Story subreddits with their content categories
STORY_SUBREDDITS = {
    "AmItheAsshole": "AITA",
    "ProRevenge": "REVENGE", 
    "pettyrevenge": "REVENGE",
    "MaliciousCompliance": "REVENGE",
    "relationship_advice": "RELATIONSHIP",
    "tifu": "STORIES",
    "entitledparents": "FAMILY_DRAMA",
    "ChoosingBeggars": "ENTITLED",
    "confession": "CONFESSION",
    "TrueOffMyChest": "CONFESSION",
    "JUSTNOMIL": "FAMILY_DRAMA",
    "BestofRedditorUpdates": "STORIES",
}


def _get_reddit_client() -> Optional['praw.Reddit']:
    """
    Creates a Reddit API client if credentials are available.
    """
    if not PRAW_AVAILABLE:
        return None
    
    client_id = getattr(config, 'REDDIT_CLIENT_ID', None) or os.getenv('REDDIT_CLIENT_ID')
    client_secret = getattr(config, 'REDDIT_CLIENT_SECRET', None) or os.getenv('REDDIT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("  Reddit API credentials not configured")
        return None
    
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="youtube_content_bot/1.0 (by /u/content_researcher)"
        )
        return reddit
    except Exception as e:
        print(f"  Failed to create Reddit client: {e}")
        return None


def scrape_subreddit_stories(
    subreddit_name: str,
    time_filter: str = "week",
    limit: int = 50,
    min_score: int = 100,
    min_words: int = 150,
    max_words: int = 600
) -> list[dict]:
    """
    Scrapes top stories from a subreddit.
    
    Args:
        subreddit_name: Name of subreddit (without r/)
        time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
        limit: Maximum posts to fetch
        min_score: Minimum upvotes required
        min_words: Minimum story length
        max_words: Maximum story length (for Shorts compatibility)
        
    Returns:
        List of story dicts with content, score, and metadata
    """
    print(f"--- [REDDIT] Scraping r/{subreddit_name} ---")
    
    reddit = _get_reddit_client()
    if not reddit:
        print("  Skipping - no Reddit client available")
        return []
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.top(time_filter=time_filter, limit=limit)
        
        stories = []
        for post in posts:
            # Skip if score too low
            if post.score < min_score:
                continue
            
            # Skip if no text content
            if not post.selftext or post.selftext == '[removed]' or post.selftext == '[deleted]':
                continue
            
            # Check word count
            word_count = len(post.selftext.split())
            if word_count < min_words or word_count > max_words:
                continue
            
            # Generate unique ID
            story_id = hashlib.md5(f"{subreddit_name}_{post.id}".encode()).hexdigest()[:12]
            
            story = {
                'id': story_id,
                'reddit_id': post.id,
                'subreddit': subreddit_name,
                'category': STORY_SUBREDDITS.get(subreddit_name, 'STORIES'),
                'title': post.title,
                'content': post.selftext,
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'word_count': word_count,
                'url': f"https://reddit.com{post.permalink}",
                'created_utc': post.created_utc,
                'scraped_at': datetime.now().isoformat(),
            }
            
            # Calculate viral potential score
            story['viral_score'] = _calculate_viral_score(story)
            
            stories.append(story)
        
        print(f"  Found {len(stories)} suitable stories")
        return stories
        
    except Exception as e:
        print(f"  Error scraping r/{subreddit_name}: {e}")
        return []


def _calculate_viral_score(story: dict) -> float:
    """
    Calculates a viral potential score for a story (0-10).
    
    Based on:
    - Upvotes (normalized)
    - Comment engagement
    - Upvote ratio
    - Word count (sweet spot around 250-400 words)
    """
    score = 0
    
    # Score from upvotes (max 4 points)
    upvotes = story.get('score', 0)
    if upvotes >= 10000:
        score += 4
    elif upvotes >= 5000:
        score += 3
    elif upvotes >= 1000:
        score += 2
    elif upvotes >= 500:
        score += 1
    
    # Score from comments (max 2 points)
    comments = story.get('num_comments', 0)
    if comments >= 500:
        score += 2
    elif comments >= 200:
        score += 1.5
    elif comments >= 100:
        score += 1
    
    # Score from upvote ratio (max 2 points)
    ratio = story.get('upvote_ratio', 0.5)
    if ratio >= 0.95:
        score += 2
    elif ratio >= 0.90:
        score += 1.5
    elif ratio >= 0.85:
        score += 1
    
    # Score from word count (max 2 points) - sweet spot is 250-400
    words = story.get('word_count', 0)
    if 250 <= words <= 400:
        score += 2
    elif 200 <= words <= 500:
        score += 1.5
    elif 150 <= words <= 600:
        score += 1
    
    return round(score, 2)


def scrape_all_subreddits(
    time_filter: str = "week",
    limit_per_sub: int = 30,
    min_score: int = 100
) -> list[dict]:
    """
    Scrapes stories from all configured subreddits.
    
    Returns:
        Combined list of stories from all subreddits, sorted by viral score
    """
    print("--- [REDDIT] Scraping all story subreddits ---")
    
    all_stories = []
    
    for subreddit_name in STORY_SUBREDDITS.keys():
        stories = scrape_subreddit_stories(
            subreddit_name=subreddit_name,
            time_filter=time_filter,
            limit=limit_per_sub,
            min_score=min_score
        )
        all_stories.extend(stories)
    
    # Sort by viral score
    all_stories.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    
    print(f"  Total stories collected: {len(all_stories)}")
    return all_stories


def get_top_stories_by_category(
    category: str,
    time_filter: str = "week",
    limit: int = 20
) -> list[dict]:
    """
    Gets top stories for a specific content category.
    
    Args:
        category: AITA, REVENGE, RELATIONSHIP, etc.
        time_filter: Reddit time filter
        limit: Max stories to return
        
    Returns:
        List of top stories for that category
    """
    print(f"--- [REDDIT] Getting top {category} stories ---")
    
    # Find subreddits for this category
    relevant_subs = [sub for sub, cat in STORY_SUBREDDITS.items() if cat == category]
    
    if not relevant_subs:
        print(f"  No subreddits found for category: {category}")
        return []
    
    all_stories = []
    for subreddit in relevant_subs:
        stories = scrape_subreddit_stories(
            subreddit_name=subreddit,
            time_filter=time_filter,
            limit=limit
        )
        all_stories.extend(stories)
    
    # Sort and limit
    all_stories.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    return all_stories[:limit]


def check_reddit_availability() -> dict:
    """
    Checks if Reddit scraping is available and configured.
    
    Returns:
        Status dict with availability and configuration info
    """
    status = {
        'praw_installed': PRAW_AVAILABLE,
        'credentials_configured': False,
        'client_works': False,
        'available': False,
    }
    
    if not PRAW_AVAILABLE:
        status['message'] = "PRAW not installed. Run: pip install praw"
        return status
    
    client_id = getattr(config, 'REDDIT_CLIENT_ID', None) or os.getenv('REDDIT_CLIENT_ID')
    client_secret = getattr(config, 'REDDIT_CLIENT_SECRET', None) or os.getenv('REDDIT_CLIENT_SECRET')
    
    if client_id and client_secret:
        status['credentials_configured'] = True
        
        # Test the client
        reddit = _get_reddit_client()
        if reddit:
            try:
                # Simple test - get subreddit info
                reddit.subreddit('AmItheAsshole').id
                status['client_works'] = True
                status['available'] = True
                status['message'] = "Reddit scraping is fully available"
            except Exception as e:
                status['message'] = f"Client error: {e}"
        else:
            status['message'] = "Failed to create Reddit client"
    else:
        status['message'] = "Reddit API credentials not configured in .env file"
    
    return status


if __name__ == '__main__':
    # Test the scraper
    print("=== Testing Reddit Scraper ===\n")
    
    # Check availability
    print("1. Checking Reddit availability:")
    status = check_reddit_availability()
    print(f"   Available: {status['available']}")
    print(f"   Message: {status['message']}")
    
    if status['available']:
        # Test subreddit scraping
        print("\n2. Scraping r/AmItheAsshole:")
        stories = scrape_subreddit_stories("AmItheAsshole", limit=10)
        for s in stories[:3]:
            print(f"   - [{s['viral_score']}] {s['title'][:50]}...")
        
        # Test category scraping
        print("\n3. Getting top REVENGE stories:")
        revenge = get_top_stories_by_category("REVENGE", limit=5)
        for s in revenge[:3]:
            print(f"   - [{s['viral_score']}] {s['title'][:50]}...")
    else:
        print("\n   Skipping tests - Reddit not available")
        print("   To enable: Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env")
