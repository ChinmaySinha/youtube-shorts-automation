# youtube_agent_system/train_story_model.py
"""
Story Model Training Pipeline

This is the main script that "trains" the content generation model by:
1. Downloading thousands of real Reddit stories from Hugging Face
2. Filtering and scoring them for quality
3. Loading the best ones into ChromaDB as training examples
4. Testing the upgraded generation with few-shot RAG prompting

Usage:
    python -m youtube_agent_system.train_story_model           # Full pipeline
    python -m youtube_agent_system.train_story_model --test     # Test only (no download)
    python -m youtube_agent_system.train_story_model --stats    # Show stats only
"""

import sys
import os
import argparse
import json

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_agent_system import knowledge_base
from youtube_agent_system.tools import dataset_downloader


def show_stats():
    """Shows current training data statistics."""
    stats = knowledge_base.get_knowledge_base_stats()
    
    print("\n" + "=" * 50)
    print("[STAT] KNOWLEDGE BASE STATS")
    print("=" * 50)
    print(f"  Training stories:    {stats.get('training_stories', 0)}")
    print(f"  Reddit stories:      {stats.get('reddit_stories', 0)}")
    print(f"  Rival videos:        {stats.get('rival_videos_analyzed', 0)}")
    print(f"  Patterns saved:      {stats.get('patterns_saved', 0)}")
    print(f"  Tutorial insights:   {stats.get('tutorial_insights', 0)}")
    print("=" * 50)
    
    return stats


def run_training_pipeline(
    max_download: int = 5000,
    top_n: int = 3000,
    min_quality: float = 3.0,
    force_redownload: bool = False
):
    """
    Runs the full training pipeline.
    
    Args:
        max_download: Max stories to download from each source
        top_n: Top N stories to keep after quality scoring
        min_quality: Minimum quality score to include
        force_redownload: If True, re-download even if corpus exists
    """
    from youtube_agent_system import config
    
    corpus_path = os.path.join(config.ASSETS_DIR, "training_corpus.json")
    
    print("=" * 60)
    print("[GO] STORY MODEL TRAINING PIPELINE")
    print("=" * 60)
    
    # Check current state
    current_count = knowledge_base.get_training_story_count()
    print(f"\n[STAT] Current training stories in ChromaDB: {current_count}")
    
    # Step 1: Download or load existing corpus
    stories = []
    
    if os.path.exists(corpus_path) and not force_redownload:
        print(f"\n[LOAD] Found existing training corpus at: {corpus_path}")
        stories = dataset_downloader.load_training_corpus(corpus_path)
        
        if len(stories) >= top_n * 0.8:  # If we already have enough
            print(f"   Already have {len(stories)} stories — skipping download")
        else:
            print(f"   Only {len(stories)} stories — downloading more...")
            stories = []  # Will re-download
    
    if not stories:
        print("\n[DL] STEP 1: Downloading stories from Hugging Face...")
        stories = dataset_downloader.run_full_download_pipeline(
            max_download=max_download,
            top_n=top_n,
            min_quality=min_quality,
            save=True
        )
    
    if not stories:
        print("[X] No stories available. Check internet connection and try again.")
        return False
    
    # Step 2: Load into ChromaDB
    print(f"\n[UP] STEP 2: Loading {len(stories)} stories into ChromaDB...")
    
    if current_count >= len(stories) * 0.9 and not force_redownload:
        print(f"   ChromaDB already has {current_count} stories — skipping reload")
    else:
        if current_count > 0:
            print(f"   Clearing existing {current_count} training stories...")
            knowledge_base.clear_training_stories()
        
        loaded = knowledge_base.save_training_stories_batch(stories)
        print(f"\n   [OK] Loaded {loaded} stories into ChromaDB")
    
    # Step 3: Verify
    print("\n[FILTER] STEP 3: Verification...")
    final_count = knowledge_base.get_training_story_count()
    print(f"   Training stories in ChromaDB: {final_count}")
    
    # Test retrieval
    print("\n   Testing story retrieval...")
    test_queries = [
        "AITA for refusing to pay for my sister's wedding",
        "My neighbor kept stealing my packages so I got revenge",
        "My mother-in-law tried to ruin my marriage",
    ]
    
    for query in test_queries:
        results = knowledge_base.get_similar_training_stories(query, n_results=2)
        if results:
            print(f"\n   Query: '{query[:50]}...'")
            for r in results:
                print(f"     -> [{r['category']}] {r['title'][:60]}... (quality: {r['quality_score']})")
        else:
            print(f"   [!] No results for: '{query[:50]}...'")
    
    # Final stats
    show_stats()
    
    print("\n" + "=" * 60)
    print(f"[OK] TRAINING COMPLETE — {final_count} stories loaded")
    print("   The content_agent will now use these as reference examples")
    print("   when generating new stories.")
    print("=" * 60)
    
    return True


def test_generation():
    """Tests story generation with the trained model."""
    from youtube_agent_system import content_agent
    
    count = knowledge_base.get_training_story_count()
    
    print("\n" + "=" * 60)
    print("[TEST] GENERATION TEST")
    print("=" * 60)
    print(f"   Training stories available: {count}")
    
    if count == 0:
        print("   [!] No training data! Run full pipeline first.")
        print("   Running: python -m youtube_agent_system.train_story_model")
        return
    
    test_topics = [
        "AITA for exposing my cheating girlfriend to her family at her own birthday party?",
        "My landlord tried to illegally evict me, so I used the law to make his life a nightmare.",
        "AITA for telling my parents I won't pay for my brother's college after they spent my tuition fund?",
    ]
    
    # Generate one story
    topic = test_topics[0]
    print(f"\n[NOTE] Generating story for: '{topic}'\n")
    
    story = content_agent.generate_story_script(topic)
    
    print("\n" + "-" * 40)
    print("GENERATED STORY:")
    print("-" * 40)
    print(story)
    print("-" * 40)
    
    # Count words
    word_count = len(story.split())
    print(f"\n[STAT] Word count: {word_count}")
    print(f"   Target range: 200-300 words")
    
    if 200 <= word_count <= 350:
        print("   [OK] Word count is in target range")
    else:
        print("   [!] Word count outside target range")


def main():
    parser = argparse.ArgumentParser(
        description="Story Model Training Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m youtube_agent_system.train_story_model              # Full training
  python -m youtube_agent_system.train_story_model --test       # Test generation
  python -m youtube_agent_system.train_story_model --stats      # Show stats
  python -m youtube_agent_system.train_story_model --force      # Re-download all
  python -m youtube_agent_system.train_story_model --top 5000   # Keep top 5000
        """
    )
    
    parser.add_argument('--test', action='store_true', 
                        help='Test generation only (no download)')
    parser.add_argument('--stats', action='store_true',
                        help='Show stats only')
    parser.add_argument('--force', action='store_true',
                        help='Force re-download even if corpus exists')
    parser.add_argument('--top', type=int, default=5000,
                        help='Number of top stories to keep (default: 5000)')
    parser.add_argument('--max-download', type=int, default=5000,
                        help='Max stories to download per source (default: 5000)')
    parser.add_argument('--min-quality', type=float, default=3.0,
                        help='Minimum quality score (default: 3.0)')
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
        return
    
    if args.test:
        show_stats()
        test_generation()
        return
    
    # Full pipeline
    success = run_training_pipeline(
        max_download=args.max_download,
        top_n=args.top,
        min_quality=args.min_quality,
        force_redownload=args.force
    )
    
    if success:
        print("\n\n[TARGET] Want to test the generation? Run:")
        print("   python -m youtube_agent_system.train_story_model --test")


if __name__ == '__main__':
    main()
