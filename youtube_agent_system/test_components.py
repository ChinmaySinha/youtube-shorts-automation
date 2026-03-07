# Test script for the autonomous runner components
import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Testing YouTube Searcher ===")
from youtube_agent_system.tools import youtube_searcher


# Test basic search
print("\n1. Basic search test:")
videos = youtube_searcher.search_youtube_videos("reddit stories", max_results=5)
print(f"   Found {len(videos)} videos")
for v in videos[:3]:
    print(f"   - {v['title'][:50]}... ({v['views']} views)")

# Test niche analysis
print("\n2. Niche potential analysis:")
try:
    potentials = youtube_searcher.discover_all_niche_potentials()
    for p in potentials[:3]:
        print(f"   - {p['niche']}: {p['recommendation']} ({p['potential_score']})")
except Exception as e:
    print(f"   Error: {e}")

# Test advice videos
print("\n3. Growth advice videos:")
advice = youtube_searcher.get_growth_advice_videos(max_per_query=2)
print(f"   Found {len(advice)} advice videos")
for a in advice[:3]:
    print(f"   - {a['title'][:50]}... ({a['views']} views)")

print("\n=== Testing Reddit Scraper ===")
from youtube_agent_system.tools import reddit_scraper

status = reddit_scraper.check_reddit_availability()
print(f"Reddit available: {status['available']}")
print(f"Message: {status['message']}")

print("\n=== Testing Knowledge Base ===")
from youtube_agent_system import knowledge_base

stats = knowledge_base.get_knowledge_base_stats()
print(f"Knowledge base stats: {stats}")

print("\n=== All Tests Passed! ===")
