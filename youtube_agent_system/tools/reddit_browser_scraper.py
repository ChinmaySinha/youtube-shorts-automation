# youtube_agent_system/tools/reddit_browser_scraper.py
"""
Browser-Based Reddit Story Scraper

Scrapes Reddit directly using the browser - NO API CREDENTIALS NEEDED!
This is the primary method for collecting viral stories from Reddit.

Works by:
1. Navigating to subreddit pages
2. Extracting post titles, content, and scores
3. Filtering for story-length content suitable for YouTube Shorts
"""

import os
import json
import hashlib
import re
from datetime import datetime
from typing import Optional, Callable

# Store for collected stories during browser sessions
_collected_stories = []


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
}


def get_subreddit_url(subreddit: str, sort: str = "top", time: str = "week") -> str:
    """
    Generates the URL for a subreddit with sorting options.
    
    Args:
        subreddit: Subreddit name (without r/)
        sort: 'hot', 'top', 'new'
        time: 'hour', 'day', 'week', 'month', 'year', 'all' (only for 'top')
    """
    base_url = f"https://old.reddit.com/r/{subreddit}"
    if sort == "top":
        return f"{base_url}/top/?t={time}"
    else:
        return f"{base_url}/{sort}/"


def parse_story_from_text(raw_text: str) -> dict:
    """
    Parses a story from raw browser-extracted text.
    """
    lines = raw_text.strip().split('\n')
    
    # Extract components
    title = ""
    score = 0
    content = ""
    
    for line in lines:
        line = line.strip()
        # Look for score patterns like "1.2k" or "500"
        score_match = re.match(r'^([\d.]+)k?$', line.lower())
        if score_match:
            score_val = float(score_match.group(1))
            if 'k' in line.lower():
                score = int(score_val * 1000)
            else:
                score = int(score_val)
        elif len(line) > 50 and not title:
            title = line
        elif len(line) > 100:
            content += line + " "
    
    return {
        'title': title,
        'score': score,
        'content': content.strip()
    }


def calculate_viral_score(story: dict) -> float:
    """
    Calculates a viral potential score for a story (0-10).
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
    
    # Score from word count (max 3 points) - sweet spot is 200-400
    content = story.get('content', '')
    words = len(content.split())
    if 200 <= words <= 400:
        score += 3
    elif 150 <= words <= 500:
        score += 2
    elif 100 <= words <= 600:
        score += 1
    
    # Score from title engagement (max 3 points)
    title = story.get('title', '').lower()
    engagement_words = ['aita', 'revenge', 'caught', 'found out', 'secret', 'finally', 
                        'karma', 'instant', 'sweet', 'satisfying', 'epic', 'best']
    title_score = sum(1 for word in engagement_words if word in title)
    score += min(title_score, 3)
    
    return round(score, 2)


def create_browser_scrape_task(subreddit: str, num_posts: int = 10) -> str:
    """
    Creates a task description for the browser subagent to scrape a subreddit.
    
    Returns:
        Task description string for browser_subagent
    """
    url = get_subreddit_url(subreddit, "top", "week")
    category = STORY_SUBREDDITS.get(subreddit, "STORIES")
    
    task = f"""
Scrape the top stories from Reddit subreddit r/{subreddit}.

Instructions:
1. Navigate to: {url}
2. For each of the top {num_posts} posts you can see:
   - Extract the post TITLE
   - Extract the SCORE (upvotes - the number on the left)
   - Click on the post to read the full content
   - Extract the full story TEXT (the self-text/body of the post)
   - Go back and continue to the next post
3. Skip any posts that are:
   - Just images or videos (no text content)
   - Very short (less than 100 words)
   - Marked as [Removed] or [Deleted]

For each valid story, format the output as:
---STORY---
TITLE: [exact title]
SCORE: [number]
SUBREDDIT: {subreddit}
CATEGORY: {category}
CONTENT: [full story text]
---END---

Return all {num_posts} stories in this format. This data will be used for YouTube content research.
"""
    return task


def parse_browser_output(output: str, subreddit: str) -> list[dict]:
    """
    Parses the browser subagent output into story dictionaries.
    
    Args:
        output: Raw output from browser subagent
        subreddit: The subreddit that was scraped
        
    Returns:
        List of story dictionaries
    """
    stories = []
    category = STORY_SUBREDDITS.get(subreddit, "STORIES")
    
    # Split by story delimiter
    story_blocks = re.split(r'---STORY---', output)
    
    for block in story_blocks:
        if '---END---' not in block:
            continue
        
        block = block.split('---END---')[0].strip()
        
        # Extract fields
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|SCORE:)', block, re.DOTALL)
        score_match = re.search(r'SCORE:\s*(\d+)', block)
        content_match = re.search(r'CONTENT:\s*(.+)', block, re.DOTALL)
        
        if title_match and content_match:
            title = title_match.group(1).strip()
            content = content_match.group(1).strip()
            score = int(score_match.group(1)) if score_match else 0
            
            # Generate ID
            story_id = hashlib.md5(f"{subreddit}_{title[:50]}".encode()).hexdigest()[:12]
            
            story = {
                'id': story_id,
                'subreddit': subreddit,
                'category': category,
                'title': title,
                'content': content,
                'score': score,
                'word_count': len(content.split()),
                'scraped_at': datetime.now().isoformat(),
            }
            
            story['viral_score'] = calculate_viral_score(story)
            stories.append(story)
    
    return stories


def add_stories_to_collection(stories: list[dict]):
    """Adds stories to the global collection."""
    global _collected_stories
    _collected_stories.extend(stories)


def get_collected_stories() -> list[dict]:
    """Returns all collected stories, sorted by viral score."""
    global _collected_stories
    _collected_stories.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    return _collected_stories


def clear_collected_stories():
    """Clears the collected stories."""
    global _collected_stories
    _collected_stories = []


def get_all_subreddit_tasks(posts_per_sub: int = 10) -> list[tuple[str, str]]:
    """
    Returns list of (subreddit, task_description) tuples for all subreddits.
    """
    tasks = []
    for subreddit in STORY_SUBREDDITS.keys():
        task = create_browser_scrape_task(subreddit, posts_per_sub)
        tasks.append((subreddit, task))
    return tasks


# Simple JavaScript to extract stories from Reddit page
REDDIT_EXTRACT_JS = """
(() => {
    const stories = [];
    const posts = document.querySelectorAll('.thing.link');
    
    posts.forEach((post, index) => {
        if (index >= 10) return;  // Limit to 10 posts
        
        const titleEl = post.querySelector('a.title');
        const scoreEl = post.querySelector('.score.unvoted');
        
        if (titleEl) {
            stories.push({
                title: titleEl.textContent,
                url: titleEl.href,
                score: scoreEl ? scoreEl.textContent : '0'
            });
        }
    });
    
    return JSON.stringify(stories);
})();
"""


if __name__ == '__main__':
    # Test the task generator
    print("=== Reddit Browser Scraper ===\n")
    
    print("Sample task for r/AmItheAsshole:")
    print("-" * 50)
    print(create_browser_scrape_task("AmItheAsshole", 5))
    
    print("\nAll subreddits to scrape:")
    for sub in STORY_SUBREDDITS.keys():
        print(f"  - r/{sub} ({STORY_SUBREDDITS[sub]})")
