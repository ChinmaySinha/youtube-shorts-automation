import os
import json
import chromadb
from . import config

# Initialize a persistent ChromaDB client.
# This stores the database on disk in the specified path.
persistent_client = chromadb.PersistentClient(
    path=os.path.join(config.ASSETS_DIR, "chroma_db")
)

# --- COLLECTION DEFINITIONS ---
# Original collection for our video performance insights
INSIGHTS_COLLECTION_NAME = "youtube_insights_v1"
insights_collection = persistent_client.get_or_create_collection(
    name=INSIGHTS_COLLECTION_NAME
)

# NEW: Collection for storing deep analysis of rival videos
RIVAL_CONTENT_COLLECTION_NAME = "rival_video_analyses_v1"
rival_collection = persistent_client.get_or_create_collection(
    name=RIVAL_CONTENT_COLLECTION_NAME
)

# NEW: Collection for synthesized content patterns (what we've learned)
CONTENT_PATTERNS_COLLECTION_NAME = "content_patterns_v1"
patterns_collection = persistent_client.get_or_create_collection(
    name=CONTENT_PATTERNS_COLLECTION_NAME
)

# NEW: Collection for Reddit stories
REDDIT_STORIES_COLLECTION_NAME = "reddit_stories_v1"
reddit_stories_collection = persistent_client.get_or_create_collection(
    name=REDDIT_STORIES_COLLECTION_NAME
)

# NEW: Collection for niche performance data
NICHE_DATA_COLLECTION_NAME = "niche_data_v1"
niche_collection = persistent_client.get_or_create_collection(
    name=NICHE_DATA_COLLECTION_NAME
)

# NEW: Collection for YouTube tutorial/advice insights
TUTORIAL_INSIGHTS_COLLECTION_NAME = "tutorial_insights_v1"
tutorial_collection = persistent_client.get_or_create_collection(
    name=TUTORIAL_INSIGHTS_COLLECTION_NAME
)

# NEW: Collection for training stories (massive curated dataset)
TRAINING_STORIES_COLLECTION_NAME = "training_stories_v1"
training_stories_collection = persistent_client.get_or_create_collection(
    name=TRAINING_STORIES_COLLECTION_NAME
)

# Backward compatibility: Keep 'collection' as alias for insights
collection = insights_collection



# ============================================================
# SECTION 1: OUR VIDEO PERFORMANCE INSIGHTS (Existing + Enhanced)
# ============================================================

def save_insight(video_id: str, insight: str, metadata: dict):
    """
    Saves or updates a performance insight in the vector database.

    Args:
        video_id: The unique ID of the video (used as the document ID).
        insight: The text of the insight (e.g., "Video '...' got X views...").
        metadata: A dictionary of structured data (views, likes, etc.).
    """
    print(f"--- [KB] Knowledge Base: Saving insight for video {video_id} ---")

    try:
        insights_collection.upsert(
            ids=[video_id],
            documents=[insight],
            metadatas=[metadata]
        )
        print("Insight saved successfully.")
    except Exception as e:
        print(f"Error saving insight to ChromaDB: {e}")


def save_insight_with_patterns(video_id: str, insight: str, metadata: dict, patterns_used: dict = None):
    """
    Enhanced: Saves a performance insight along with which patterns were used.
    This enables correlation between patterns and performance.
    
    Args:
        video_id: The unique ID of the video.
        insight: The text insight about performance.
        metadata: Structured data (views, likes, etc.).
        patterns_used: Dictionary of patterns that were applied to this video.
    """
    print(f"--- [KB] Knowledge Base: Saving insight with patterns for video {video_id} ---")
    
    # Flatten patterns into metadata for storage
    enhanced_metadata = metadata.copy()
    if patterns_used:
        enhanced_metadata['patterns_used'] = json.dumps(patterns_used)
        enhanced_metadata['hook_technique'] = patterns_used.get('hook_technique', '')
        enhanced_metadata['content_category'] = patterns_used.get('content_category', '')
        enhanced_metadata['payoff_type'] = patterns_used.get('payoff_type', '')
    
    try:
        insights_collection.upsert(
            ids=[video_id],
            documents=[insight],
            metadatas=[enhanced_metadata]
        )
        print("Insight with patterns saved successfully.")
    except Exception as e:
        print(f"Error saving insight to ChromaDB: {e}")


def query_insights(query: str, n_results: int = 3) -> list[str]:
    """
    Queries the knowledge base for insights most relevant to a text query.
    """
    print(f"--- [KB] Knowledge Base: Querying for '{query}' with {n_results} results ---")
    try:
        results = insights_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] if results.get('documents') else []
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []


def get_all_insights() -> list[str]:
    """
    Retrieves all insights currently stored in the knowledge base.
    """
    print("--- [KB] Knowledge Base: Retrieving all insights ---")
    try:
        all_items = insights_collection.get(include=["documents"])
        return all_items['documents'] if all_items else []
    except Exception as e:
        print(f"Error getting all insights from ChromaDB: {e}")
        return []


def get_all_insights_with_metadata() -> list[dict]:
    """
    Retrieves all insights with their full metadata for analysis.
    
    Returns:
        List of dicts with 'id', 'document', and 'metadata' keys.
    """
    print("--- [KB] Knowledge Base: Retrieving all insights with metadata ---")
    try:
        all_items = insights_collection.get(include=["documents", "metadatas"])
        if not all_items or not all_items.get('ids'):
            return []
        
        results = []
        for i, vid in enumerate(all_items['ids']):
            results.append({
                'id': vid,
                'document': all_items['documents'][i] if all_items.get('documents') else '',
                'metadata': all_items['metadatas'][i] if all_items.get('metadatas') else {}
            })
        return results
    except Exception as e:
        print(f"Error getting insights with metadata: {e}")
        return []


def get_pattern_performance_correlation() -> dict:
    """
    Analyzes which patterns correlate with high/low performance.
    
    Returns:
        Dictionary mapping patterns to their average performance scores.
    """
    insights = get_all_insights_with_metadata()
    
    pattern_stats = {}
    
    for insight in insights:
        metadata = insight.get('metadata', {})
        views = metadata.get('views', 0)
        likes = metadata.get('likes', 0)
        
        # Calculate simple performance score
        score = views + (likes * 10)  # Weight likes more
        
        # Track by hook technique
        hook = metadata.get('hook_technique', 'unknown')
        if hook not in pattern_stats:
            pattern_stats[hook] = {'total_score': 0, 'count': 0}
        pattern_stats[hook]['total_score'] += score
        pattern_stats[hook]['count'] += 1
        
        # Track by content category
        category = metadata.get('content_category', 'unknown')
        if category not in pattern_stats:
            pattern_stats[category] = {'total_score': 0, 'count': 0}
        pattern_stats[category]['total_score'] += score
        pattern_stats[category]['count'] += 1
    
    # Calculate averages
    for key in pattern_stats:
        count = pattern_stats[key]['count']
        if count > 0:
            pattern_stats[key]['avg_score'] = pattern_stats[key]['total_score'] / count
    
    return pattern_stats


# ============================================================
# SECTION 2: RIVAL VIDEO ANALYSES (NEW)
# ============================================================

def save_rival_analysis(video_id: str, video_url: str, analysis_data: dict, metadata: dict = None):
    """
    Saves a deep analysis of a rival video to the knowledge base.
    
    Args:
        video_id: Unique identifier for the video (can be YouTube ID or URL hash).
        video_url: The source URL of the analyzed video.
        analysis_data: The structured analysis from Gemini (transcript, hooks, etc.).
        metadata: Additional metadata (channel name, view count, etc.).
    """
    print(f"--- [KB] Knowledge Base: Saving rival analysis for {video_id} ---")
    
    # Create a searchable document from the analysis
    document_parts = []
    if analysis_data.get('transcript'):
        document_parts.append(f"Transcript: {analysis_data['transcript']}")
    if analysis_data.get('hook', {}).get('text'):
        document_parts.append(f"Hook: {analysis_data['hook']['text']}")
    if analysis_data.get('what_makes_it_work'):
        document_parts.append(f"Why it works: {analysis_data['what_makes_it_work']}")
    
    document = "\n".join(document_parts) if document_parts else json.dumps(analysis_data)
    
    # Build metadata
    full_metadata = metadata.copy() if metadata else {}
    full_metadata['video_url'] = video_url
    full_metadata['content_category'] = analysis_data.get('content_category', 'OTHER')
    full_metadata['hook_technique'] = analysis_data.get('hook', {}).get('technique', '')
    full_metadata['payoff_type'] = analysis_data.get('story_structure', {}).get('payoff_type', '')
    full_metadata['view_appeal'] = analysis_data.get('estimated_view_appeal', 0)
    full_metadata['full_analysis'] = json.dumps(analysis_data)  # Store full analysis as JSON
    
    try:
        rival_collection.upsert(
            ids=[video_id],
            documents=[document],
            metadatas=[full_metadata]
        )
        print(f"Rival analysis saved. Category: {full_metadata['content_category']}")
    except Exception as e:
        print(f"Error saving rival analysis: {e}")


def get_all_rival_analyses() -> list[dict]:
    """
    Retrieves all stored rival video analyses.
    
    Returns:
        List of analysis dictionaries with full data.
    """
    print("--- [KB] Knowledge Base: Retrieving all rival analyses ---")
    try:
        all_items = rival_collection.get(include=["documents", "metadatas"])
        if not all_items or not all_items.get('ids'):
            return []
        
        results = []
        for i, vid in enumerate(all_items['ids']):
            metadata = all_items['metadatas'][i] if all_items.get('metadatas') else {}
            # Parse the full analysis from JSON
            full_analysis = {}
            if metadata.get('full_analysis'):
                try:
                    full_analysis = json.loads(metadata['full_analysis'])
                except:
                    pass
            
            results.append({
                'id': vid,
                'video_url': metadata.get('video_url', ''),
                'content_category': metadata.get('content_category', ''),
                'hook_technique': metadata.get('hook_technique', ''),
                'payoff_type': metadata.get('payoff_type', ''),
                'view_appeal': metadata.get('view_appeal', 0),
                'full_analysis': full_analysis
            })
        
        print(f"Retrieved {len(results)} rival analyses.")
        return results
    except Exception as e:
        print(f"Error getting rival analyses: {e}")
        return []


def query_rival_content(query: str, n_results: int = 5) -> list[dict]:
    """
    Searches rival content for similar themes/topics.
    
    Args:
        query: Search query (e.g., "revenge stories", "family drama").
        n_results: Number of results to return.
        
    Returns:
        List of matching rival analyses.
    """
    print(f"--- [KB] Knowledge Base: Searching rival content for '{query}' ---")
    try:
        results = rival_collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas"]
        )
        
        if not results.get('ids') or not results['ids'][0]:
            return []
        
        output = []
        for i, vid in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
            output.append({
                'id': vid,
                'document': results['documents'][0][i] if results.get('documents') else '',
                'metadata': metadata
            })
        
        return output
    except Exception as e:
        print(f"Error querying rival content: {e}")
        return []


def get_rival_count() -> int:
    """Returns the number of rival videos analyzed."""
    try:
        count = rival_collection.count()
        return count
    except:
        return 0


# ============================================================
# SECTION 3: CONTENT PATTERNS (NEW)
# ============================================================

def save_synthesized_patterns(patterns: dict, pattern_id: str = "latest"):
    """
    Saves synthesized content patterns derived from rival analysis.
    
    These patterns represent what we've learned about successful content.
    
    Args:
        patterns: Dictionary of patterns (from gemini_analyzer.extract_patterns_from_analyses).
        pattern_id: Identifier for this pattern set (default: "latest" for most recent).
    """
    print(f"--- [KB] Knowledge Base: Saving synthesized patterns ({pattern_id}) ---")
    
    # Create searchable document from patterns
    document = f"""
    Content Patterns Summary:
    - Top Category: {patterns.get('most_popular_category', 'unknown')}
    - Top Hook Technique: {patterns.get('most_effective_hook_technique', 'unknown')}
    - Top Payoff Type: {patterns.get('most_common_payoff', 'unknown')}
    - Sample Size: {patterns.get('sample_size', 0)} videos
    - High Performers: {patterns.get('high_performers_count', 0)} videos
    """
    
    metadata = {
        'sample_size': patterns.get('sample_size', 0),
        'high_performers_count': patterns.get('high_performers_count', 0),
        'top_category': patterns.get('most_popular_category', ''),
        'top_hook': patterns.get('most_effective_hook_technique', ''),
        'top_payoff': patterns.get('most_common_payoff', ''),
        'full_patterns': json.dumps(patterns)
    }
    
    try:
        patterns_collection.upsert(
            ids=[pattern_id],
            documents=[document],
            metadatas=[metadata]
        )
        print("Patterns saved successfully.")
    except Exception as e:
        print(f"Error saving patterns: {e}")


def get_latest_patterns() -> dict | None:
    """
    Retrieves the most recently saved content patterns.
    
    Returns:
        Dictionary of patterns, or None if no patterns exist.
    """
    print("--- [KB] Knowledge Base: Retrieving latest patterns ---")
    try:
        result = patterns_collection.get(
            ids=["latest"],
            include=["metadatas"]
        )
        
        if result and result.get('metadatas') and result['metadatas'][0]:
            metadata = result['metadatas'][0]
            if metadata.get('full_patterns'):
                patterns = json.loads(metadata['full_patterns'])
                print(f"Patterns found. Sample size: {patterns.get('sample_size', 0)}")
                return patterns
        
        print("No patterns found.")
        return None
    except Exception as e:
        print(f"Error getting patterns: {e}")
        return None


def get_content_recommendation() -> dict:
    """
    Returns a content recommendation based on learned patterns.
    
    This is the main interface for the Strategy Agent to get guidance.
    
    Returns:
        Dictionary with recommended content parameters.
    """
    patterns = get_latest_patterns()
    
    if not patterns:
        return {
            "status": "no_data",
            "message": "No patterns learned yet. Run rival analysis first.",
            "use_fallback": True
        }
    
    recommendation = patterns.get('recommendation', {})
    
    # Enhance with example hooks if available
    example_hooks = patterns.get('example_hooks', [])
    
    return {
        "status": "ready",
        "content_category": recommendation.get('content_category', 'AITA'),
        "hook_style": recommendation.get('hook_style', 'shocking revelation'),
        "payoff_type": recommendation.get('payoff_type', 'justice served'),
        "target_emotion": recommendation.get('target_emotion', 'satisfaction'),
        "example_hooks": example_hooks,
        "sample_size": patterns.get('sample_size', 0),
        "confidence": min(patterns.get('sample_size', 0) / 10, 1.0),  # More samples = higher confidence
        "use_fallback": False
    }


# ============================================================
# SECTION 4: UTILITY FUNCTIONS
# ============================================================

def get_knowledge_base_stats() -> dict:
    """
    Returns statistics about the knowledge base contents.
    """
    return {
        'our_videos_analyzed': insights_collection.count(),
        'rival_videos_analyzed': rival_collection.count(),
        'patterns_saved': patterns_collection.count(),
        'reddit_stories': reddit_stories_collection.count(),
        'niches_tracked': niche_collection.count(),
        'tutorial_insights': tutorial_collection.count(),
        'training_stories': training_stories_collection.count(),
    }



def clear_rival_data():
    """Clears all rival analysis data (use with caution)."""
    print("--- [!] Clearing all rival analysis data ---")
    try:
        persistent_client.delete_collection(RIVAL_CONTENT_COLLECTION_NAME)
        global rival_collection
        rival_collection = persistent_client.get_or_create_collection(
            name=RIVAL_CONTENT_COLLECTION_NAME
        )
        print("Rival data cleared.")
    except Exception as e:
        print(f"Error clearing rival data: {e}")


# ============================================================
# SECTION 5: REDDIT STORIES (NEW)
# ============================================================

def save_reddit_story(story_id: str, story_data: dict, metadata: dict = None):
    """
    Saves a Reddit story to the knowledge base.
    
    Args:
        story_id: Unique identifier for the story
        story_data: Dictionary with story content, title, score, etc.
        metadata: Additional metadata (subreddit, category, etc.)
    """
    print(f"--- [KB] Knowledge Base: Saving Reddit story {story_id} ---")
    
    # Create searchable document
    document = f"""
    Title: {story_data.get('title', '')}
    Subreddit: {story_data.get('subreddit', '')}
    Content: {story_data.get('content', '')}
    """
    
    # Build metadata
    full_metadata = metadata.copy() if metadata else {}
    full_metadata['title'] = story_data.get('title', '')
    full_metadata['subreddit'] = story_data.get('subreddit', '')
    full_metadata['score'] = story_data.get('score', 0)
    full_metadata['viral_score'] = story_data.get('viral_score', 0)
    full_metadata['word_count'] = story_data.get('word_count', 0)
    full_metadata['url'] = story_data.get('url', '')
    full_metadata['full_story'] = json.dumps(story_data)
    
    try:
        reddit_stories_collection.upsert(
            ids=[story_id],
            documents=[document],
            metadatas=[full_metadata]
        )
        print(f"Reddit story saved. Score: {full_metadata['score']}")
    except Exception as e:
        print(f"Error saving Reddit story: {e}")


def get_top_reddit_stories(category: str = None, n: int = 10) -> list[dict]:
    """
    Retrieves top Reddit stories from the knowledge base.
    
    Args:
        category: Filter by category (AITA, REVENGE, etc.) or None for all
        n: Number of stories to return
        
    Returns:
        List of story dictionaries sorted by viral score
    """
    print(f"--- [KB] Knowledge Base: Getting top Reddit stories ({category or 'all'}) ---")
    
    try:
        all_items = reddit_stories_collection.get(include=["documents", "metadatas"])
        if not all_items or not all_items.get('ids'):
            return []
        
        stories = []
        for i, sid in enumerate(all_items['ids']):
            metadata = all_items['metadatas'][i] if all_items.get('metadatas') else {}
            
            # Filter by category if specified
            if category and metadata.get('category') != category:
                continue
            
            # Parse full story
            full_story = {}
            if metadata.get('full_story'):
                try:
                    full_story = json.loads(metadata['full_story'])
                except:
                    pass
            
            stories.append({
                'id': sid,
                'title': metadata.get('title', ''),
                'category': metadata.get('category', ''),
                'viral_score': metadata.get('viral_score', 0),
                'score': metadata.get('score', 0),
                'full_story': full_story
            })
        
        # Sort by viral score
        stories.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
        return stories[:n]
        
    except Exception as e:
        print(f"Error getting Reddit stories: {e}")
        return []


def get_reddit_story_count() -> int:
    """Returns the number of Reddit stories stored."""
    try:
        return reddit_stories_collection.count()
    except:
        return 0


# ============================================================
# SECTION 6: NICHE PERFORMANCE DATA (NEW)
# ============================================================

def save_niche_data(niche: str, metrics: dict):
    """
    Saves performance data for a content niche.
    
    Args:
        niche: Niche name (AITA, REVENGE, etc.)
        metrics: Performance metrics (avg_views, competition, etc.)
    """
    print(f"--- [KB] Knowledge Base: Saving niche data for {niche} ---")
    
    document = f"""
    Niche: {niche}
    Potential Score: {metrics.get('potential_score', 0)}
    Average Views: {metrics.get('average_views', 0)}
    Competition: {metrics.get('unique_channels', 0)} channels
    """
    
    metadata = {
        'niche': niche,
        'potential_score': metrics.get('potential_score', 0),
        'average_views': metrics.get('average_views', 0),
        'max_views': metrics.get('max_views', 0),
        'unique_channels': metrics.get('unique_channels', 0),
        'videos_analyzed': metrics.get('videos_analyzed', 0),
        'recommendation': metrics.get('recommendation', ''),
        'updated_at': json.dumps({'timestamp': __import__('datetime').datetime.now().isoformat()})
    }
    
    try:
        niche_collection.upsert(
            ids=[niche.upper()],
            documents=[document],
            metadatas=[metadata]
        )
        print(f"Niche data saved: {niche} = {metrics.get('recommendation', 'N/A')}")
    except Exception as e:
        print(f"Error saving niche data: {e}")


def get_best_niches(n: int = 5) -> list[dict]:
    """
    Gets the best performing niches based on stored data.
    
    Returns:
        List of niche dictionaries sorted by potential score
    """
    print("--- [KB] Knowledge Base: Getting best niches ---")
    
    try:
        all_items = niche_collection.get(include=["metadatas"])
        if not all_items or not all_items.get('ids'):
            return []
        
        niches = []
        for i, nid in enumerate(all_items['ids']):
            metadata = all_items['metadatas'][i] if all_items.get('metadatas') else {}
            niches.append({
                'niche': metadata.get('niche', nid),
                'potential_score': metadata.get('potential_score', 0),
                'average_views': metadata.get('average_views', 0),
                'recommendation': metadata.get('recommendation', ''),
            })
        
        # Sort by potential score
        niches.sort(key=lambda x: x.get('potential_score', 0), reverse=True)
        return niches[:n]
        
    except Exception as e:
        print(f"Error getting niches: {e}")
        return []


# ============================================================
# SECTION 7: TUTORIAL INSIGHTS (NEW)
# ============================================================

def save_tutorial_insight(video_id: str, insights: dict):
    """
    Saves insights learned from a YouTube tutorial/advice video.
    
    Args:
        video_id: YouTube video ID
        insights: Dictionary with title, analysis, key takeaways
    """
    print(f"--- [KB] Knowledge Base: Saving tutorial insight {video_id} ---")
    
    # Extract key info
    title = insights.get('title', '')
    analysis = insights.get('analysis', {})
    
    document = f"""
    Tutorial: {title}
    Views: {insights.get('views', 0)}
    Key Insights: {analysis.get('what_makes_it_work', '')}
    """
    
    metadata = {
        'title': title,
        'views': insights.get('views', 0),
        'query': insights.get('query', ''),
        'full_insights': json.dumps(insights)
    }
    
    try:
        tutorial_collection.upsert(
            ids=[video_id],
            documents=[document],
            metadatas=[metadata]
        )
        print(f"Tutorial insight saved: {title[:50]}...")
    except Exception as e:
        print(f"Error saving tutorial insight: {e}")


def get_tutorial_insights(n: int = 10) -> list[dict]:
    """
    Retrieves stored tutorial insights.
    
    Returns:
        List of insight dictionaries
    """
    print("--- [KB] Knowledge Base: Getting tutorial insights ---")
    
    try:
        all_items = tutorial_collection.get(include=["documents", "metadatas"])
        if not all_items or not all_items.get('ids'):
            return []
        
        insights = []
        for i, tid in enumerate(all_items['ids']):
            metadata = all_items['metadatas'][i] if all_items.get('metadatas') else {}
            
            full_insights = {}
            if metadata.get('full_insights'):
                try:
                    full_insights = json.loads(metadata['full_insights'])
                except:
                    pass
            
            insights.append({
                'id': tid,
                'title': metadata.get('title', ''),
                'views': metadata.get('views', 0),
                'query': metadata.get('query', ''),
                'full_insights': full_insights
            })
        
        # Sort by views
        insights.sort(key=lambda x: x.get('views', 0), reverse=True)
        return insights[:n]
        
    except Exception as e:
        print(f"Error getting tutorial insights: {e}")
        return []


def get_tutorial_count() -> int:
    """Returns the number of tutorial insights stored."""
    try:
        return tutorial_collection.count()
    except:
        return 0


# ============================================================
# SECTION 8: TRAINING STORIES (Massive curated dataset)
# ============================================================

def save_training_stories_batch(stories: list[dict], batch_size: int = 200) -> int:
    """
    Bulk-loads curated training stories into ChromaDB.
    
    This is the core of the "training" pipeline -- these stories
    serve as few-shot examples for the content generation model.
    
    Args:
        stories: List of story dicts with 'id', 'title', 'body', 'category', etc.
        batch_size: How many to insert per ChromaDB batch call
        
    Returns:
        Number of stories successfully loaded
    """
    print(f"--- [KB] Loading {len(stories)} training stories into ChromaDB ---")
    
    loaded = 0
    seen_ids = set()  # Global dedup across all batches
    
    for i in range(0, len(stories), batch_size):
        batch = stories[i:i + batch_size]
        
        ids = []
        documents = []
        metadatas = []
        
        for story in batch:
            story_id = story.get('id', f'train_{i}_{loaded}')
            
            # Skip duplicate IDs
            if story_id in seen_ids:
                continue
            seen_ids.add(story_id)
            
            title = story.get('title', '')
            body = story.get('body', '') or story.get('content', '')
            category = story.get('category', 'STORIES')
            
            if not body or len(body.strip()) < 50:
                continue
            
            # Build searchable document (title + body for embedding)
            document = f"Title: {title}\n\n{body}"
            
            metadata = {
                'title': title[:500],  # ChromaDB has metadata size limits
                'category': category,
                'quality_score': story.get('quality_score', 0),
                'word_count': story.get('word_count', len(body.split())),
                'score': story.get('score', 0),
                'source': story.get('source', 'unknown'),
            }
            
            ids.append(story_id)
            documents.append(document)
            metadatas.append(metadata)
        
        if ids:
            try:
                training_stories_collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                loaded += len(ids)
            except Exception as e:
                print(f"   [!] Batch error at position {i}: {e}")
        
        # Progress update every 500 stories
        if loaded % 500 < batch_size:
            print(f"   ... loaded {loaded} stories so far")
    
    print(f"[OK] Successfully loaded {loaded} training stories into ChromaDB")
    return loaded


def get_similar_training_stories(
    query: str,
    category: str = None,
    n_results: int = 5
) -> list[dict]:
    """
    Retrieves training stories most similar to a given query/topic.
    
    This is the key function used by content_agent to get few-shot examples.
    
    Args:
        query: Topic or theme to find similar stories for
        category: Optional category filter (AITA, REVENGE, etc.)
        n_results: Number of stories to return
        
    Returns:
        List of story dicts with 'title', 'body', 'category', 'quality_score'
    """
    try:
        count = training_stories_collection.count()
        if count == 0:
            return []
        
        # Build query parameters
        query_params = {
            'query_texts': [query],
            'n_results': min(n_results, count),
            'include': ['documents', 'metadatas']
        }
        
        # Add category filter if specified
        if category:
            query_params['where'] = {'category': category}
        
        results = training_stories_collection.query(**query_params)
        
        if not results.get('ids') or not results['ids'][0]:
            return []
        
        stories = []
        for i, sid in enumerate(results['ids'][0]):
            doc = results['documents'][0][i] if results.get('documents') else ''
            metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
            
            # Extract body from document (remove "Title: ..." prefix)
            body = doc
            if body.startswith('Title: '):
                # Split on first double newline to separate title from body
                parts = body.split('\n\n', 1)
                body = parts[1] if len(parts) > 1 else parts[0]
            
            stories.append({
                'id': sid,
                'title': metadata.get('title', ''),
                'body': body,
                'category': metadata.get('category', ''),
                'quality_score': metadata.get('quality_score', 0),
                'word_count': metadata.get('word_count', 0),
            })
        
        return stories
        
    except Exception as e:
        print(f"Error querying training stories: {e}")
        return []


def get_training_story_count() -> int:
    """Returns the number of training stories loaded."""
    try:
        return training_stories_collection.count()
    except:
        return 0


def get_random_training_story(category: str = None) -> dict | None:
    """
    Retrieves a random real Reddit story from the training database.
    
    Unlike get_similar_training_stories (which searches by similarity),
    this picks a random high-quality story for direct use as narration content.
    
    Args:
        category: Optional category filter (AITA, REVENGE, FAMILY_DRAMA, etc.)
        
    Returns:
        A story dict with 'title', 'body', 'category', 'quality_score',
        or None if no stories are available.
    """
    import random
    
    try:
        count = training_stories_collection.count()
        if count == 0:
            return None
        
        # Use a random query to get varied results each time
        random_queries = [
            "shocking betrayal family secret", "revenge karma justice",
            "entitled person gets what they deserve", "relationship drama",
            "cheating partner caught exposed", "family drama inheritance",
            "workplace revenge boss fired", "roommate nightmare story",
            "wedding disaster revenge", "neighbor dispute escalation",
            "best friend betrayal", "in-laws toxic behavior",
        ]
        random_query = random.choice(random_queries)
        
        # Query more than we need so we can pick the BEST ones
        query_params = {
            'query_texts': [random_query],
            'n_results': min(50, count),
            'include': ['documents', 'metadatas']
        }
        
        # Add category filter if specified
        if category:
            query_params['where'] = {'category': category}
        
        results = training_stories_collection.query(**query_params)
        
        if not results.get('ids') or not results['ids'][0]:
            # If category filter returned nothing, try without filter
            if category:
                del query_params['where']
                results = training_stories_collection.query(**query_params)
                if not results.get('ids') or not results['ids'][0]:
                    return None
            else:
                return None
        
        # Sort by quality score and pick from the BEST stories
        scored_indices = []
        for j in range(len(results['ids'][0])):
            meta = results['metadatas'][0][j] if results.get('metadatas') else {}
            score = meta.get('quality_score', 0)
            wc = meta.get('word_count', 0)
            # Only high-quality stories with good length
            if isinstance(score, (int, float)) and score >= 3.0 and wc > 100:
                scored_indices.append((j, score))
        
        if scored_indices:
            # Sort by quality score descending, pick randomly from top 5
            scored_indices.sort(key=lambda x: x[1], reverse=True)
            top_n = scored_indices[:min(5, len(scored_indices))]
            idx = random.choice(top_n)[0]
        else:
            idx = random.randint(0, len(results['ids'][0]) - 1)
        
        doc = results['documents'][0][idx] if results.get('documents') else ''
        metadata = results['metadatas'][0][idx] if results.get('metadatas') else {}
        
        # Extract body from document (remove "Title: ..." prefix)
        body = doc
        if body.startswith('Title: '):
            parts = body.split('\n\n', 1)
            body = parts[1] if len(parts) > 1 else parts[0]
        
        story = {
            'id': results['ids'][0][idx],
            'title': metadata.get('title', ''),
            'body': body,
            'category': metadata.get('category', ''),
            'quality_score': metadata.get('quality_score', 0),
            'word_count': metadata.get('word_count', 0),
        }
        
        print(f"--- [KB] Retrieved real story: '{story['title'][:60]}...' ({story['category']}, {story['word_count']} words) ---")
        return story
        
    except Exception as e:
        print(f"Error retrieving random training story: {e}")
        return None


def clear_training_stories():
    """Clears all training stories (use with caution)."""
    print("--- [!] Clearing all training stories ---")
    try:
        global training_stories_collection
        persistent_client.delete_collection(TRAINING_STORIES_COLLECTION_NAME)
        training_stories_collection = persistent_client.get_or_create_collection(
            name=TRAINING_STORIES_COLLECTION_NAME
        )
        print("Training stories cleared.")
    except Exception as e:
        print(f"Error clearing training stories: {e}")



if __name__ == '__main__':
    # Example of how the enhanced knowledge base would be used.
    print("--- Testing Enhanced Knowledge Base ---")
    
    # Show stats
    stats = get_knowledge_base_stats()
    print(f"\nCurrent stats: {stats}")
    
    # Test saving rival analysis
    test_analysis = {
        'transcript': 'My sister tried to steal my inheritance...',
        'hook': {'text': 'The DNA test changed everything.', 'technique': 'shocking revelation'},
        'content_category': 'FAMILY_DRAMA',
        'story_structure': {'payoff_type': 'justice served'},
        'estimated_view_appeal': 8,
        'what_makes_it_work': 'Strong emotional hook with satisfying payoff'
    }
    save_rival_analysis('test_video_1', 'https://youtube.com/shorts/test', test_analysis, {'channel': 'TestChannel'})
    
    # Test getting recommendation
    print("\n--- Content Recommendation ---")
    rec = get_content_recommendation()
    print(json.dumps(rec, indent=2))
    
    # Show updated stats
    stats = get_knowledge_base_stats()
    print(f"\nUpdated stats: {stats}")

