# youtube_agent_system/tools/gemini_analyzer.py
"""
Gemini Video Analyzer Tool

Uses Google's Gemini 2.0 Flash to deeply analyze YouTube videos and extract:
- Full transcript/narrative
- Hook strategy (first 3 seconds)
- Story structure (setup, conflict, twist, resolution)
- Emotional beats and tone progression
- Pacing analysis
- Engagement triggers (cliffhangers, reveals, payoffs)

This tool is used for LEARNING from rival content, NOT for generating videos.
"""

import json
import re
import google.generativeai as genai
from .. import config


def _get_gemini_client():
    """Initialize and return Gemini client."""
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in .env file")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    return genai.GenerativeModel(config.GEMINI_MODEL)


# The main analysis prompt - extracts structured content patterns
VIDEO_ANALYSIS_PROMPT = """
You are an expert content analyst specializing in viral YouTube Shorts, particularly Reddit story content (AITA, Revenge stories, Relationship drama, etc.).

Analyze this YouTube video and extract the following information in a structured JSON format:

{
    "transcript": "The full spoken text/narration from the video",
    
    "hook": {
        "text": "The exact first sentence or two that hooks the viewer",
        "technique": "Name the hook technique (e.g., 'shocking revelation', 'mystery question', 'controversial statement', 'emotional trauma')",
        "rating": 1-10
    },
    
    "story_structure": {
        "setup": "Brief description of the situation/context",
        "conflict": "What's the main problem/drama?",
        "twist": "Any unexpected turn? (null if none)",
        "resolution": "How does it end?",
        "payoff_type": "Type of ending (e.g., 'revenge satisfied', 'justice served', 'wholesome', 'cliffhanger', 'validation')"
    },
    
    "emotional_arc": {
        "starting_emotion": "What emotion does the story start with?",
        "peak_emotion": "What's the strongest emotion triggered?",
        "ending_emotion": "What emotion is the viewer left with?",
        "emotion_journey": ["list", "of", "emotions", "in", "order"]
    },
    
    "content_category": "One of: AITA, REVENGE, RELATIONSHIP, FAMILY_DRAMA, WORKPLACE, KARMA, WHOLESOME, MYSTERY, OTHER",
    
    "pacing": {
        "words_per_minute_estimate": "fast/medium/slow",
        "dramatic_pauses": true/false,
        "sentence_length": "short/medium/long"
    },
    
    "engagement_triggers": [
        "List specific moments designed to keep viewers watching",
        "e.g., 'cliffhanger at 0:15', 'shocking reveal at 0:45'"
    ],
    
    "what_makes_it_work": "1-2 sentences explaining why this video is engaging",
    
    "estimated_view_appeal": 1-10
}

Be precise with the transcript - capture the actual narration.
If you can't determine something, use null instead of guessing.
Return ONLY valid JSON, no other text.
"""


def analyze_youtube_video(video_url: str) -> dict | None:
    """
    Analyzes a YouTube video using Gemini and extracts structured content patterns.
    
    Args:
        video_url: The YouTube video URL (must be public)
        
    Returns:
        A dictionary with extracted content patterns, or None on failure.
    """
    print(f"--- [SCAN] Gemini Analyzer: Analyzing video {video_url} ---")
    
    try:
        from google import genai
        from google.genai import types
        
        # Initialize client with new API
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        # Create the request with proper YouTube URL format
        # Using gemini-2.5-flash - the most capable model with video understanding
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=types.Content(
                parts=[
                    types.Part(
                        file_data=types.FileData(file_uri=video_url)
                    ),
                    types.Part(text=VIDEO_ANALYSIS_PROMPT)
                ]
            )
        )
        
        # Parse the JSON response
        response_text = response.text.strip()
        
        # Clean up the response - remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        analysis = json.loads(response_text)
        
        print(f"--- [OK] Analysis complete for: {video_url} ---")
        print(f"    Category: {analysis.get('content_category', 'Unknown')}")
        print(f"    Hook technique: {analysis.get('hook', {}).get('technique', 'Unknown')}")
        print(f"    View appeal: {analysis.get('estimated_view_appeal', 'N/A')}/10")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"--- [X] Failed to parse Gemini response as JSON: {e} ---")
        print(f"Raw response: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"--- [X] Gemini analysis failed for {video_url}: {e} ---")
        import traceback
        traceback.print_exc()
        return None


def analyze_multiple_videos(video_urls: list[str]) -> list[dict]:
    """
    Analyzes multiple videos and returns all successful analyses.
    
    Args:
        video_urls: List of YouTube video URLs
        
    Returns:
        List of analysis dictionaries (skips failed analyses)
    """
    analyses = []
    
    for url in video_urls:
        analysis = analyze_youtube_video(url)
        if analysis:
            analysis['source_url'] = url
            analyses.append(analysis)
    
    print(f"--- [STATS] Analyzed {len(analyses)}/{len(video_urls)} videos successfully ---")
    return analyses


def extract_patterns_from_analyses(analyses: list[dict]) -> dict:
    """
    Synthesizes patterns from multiple video analyses to identify what works.
    
    Args:
        analyses: List of video analysis dictionaries
        
    Returns:
        A dictionary of synthesized patterns and recommendations
    """
    if not analyses:
        return {"error": "No analyses provided"}
    
    print(f"--- [DNA] Extracting patterns from {len(analyses)} video analyses ---")
    
    # Aggregate data
    hook_techniques = {}
    content_categories = {}
    payoff_types = {}
    emotions = {}
    high_performers = []  # View appeal >= 7
    
    for analysis in analyses:
        # Count hook techniques
        hook_tech = analysis.get('hook', {}).get('technique', 'unknown')
        hook_techniques[hook_tech] = hook_techniques.get(hook_tech, 0) + 1
        
        # Count content categories
        category = analysis.get('content_category', 'OTHER')
        content_categories[category] = content_categories.get(category, 0) + 1
        
        # Count payoff types
        payoff = analysis.get('story_structure', {}).get('payoff_type', 'unknown')
        payoff_types[payoff] = payoff_types.get(payoff, 0) + 1
        
        # Track ending emotions
        end_emotion = analysis.get('emotional_arc', {}).get('ending_emotion', 'unknown')
        emotions[end_emotion] = emotions.get(end_emotion, 0) + 1
        
        # Track high performers
        view_appeal = analysis.get('estimated_view_appeal', 0)
        if view_appeal >= 7:
            high_performers.append(analysis)
    
    # Sort by frequency
    top_hook = max(hook_techniques, key=hook_techniques.get) if hook_techniques else "unknown"
    top_category = max(content_categories, key=content_categories.get) if content_categories else "OTHER"
    top_payoff = max(payoff_types, key=payoff_types.get) if payoff_types else "unknown"
    top_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
    
    # Extract example hooks from high performers
    example_hooks = []
    for hp in high_performers[:3]:
        hook_text = hp.get('hook', {}).get('text', '')
        if hook_text:
            example_hooks.append(hook_text)
    
    patterns = {
        "sample_size": len(analyses),
        "high_performers_count": len(high_performers),
        
        "most_effective_hook_technique": top_hook,
        "hook_techniques_distribution": hook_techniques,
        "example_hooks": example_hooks,
        
        "most_popular_category": top_category,
        "category_distribution": content_categories,
        
        "most_common_payoff": top_payoff,
        "payoff_distribution": payoff_types,
        
        "preferred_ending_emotion": top_emotion,
        "emotion_distribution": emotions,
        
        "recommendation": {
            "content_category": top_category,
            "hook_style": top_hook,
            "payoff_type": top_payoff,
            "target_emotion": top_emotion,
            "example_hooks_to_emulate": example_hooks
        }
    }
    
    print(f"--- [TARGET] Pattern extraction complete ---")
    print(f"    Top category: {top_category}")
    print(f"    Top hook technique: {top_hook}")
    print(f"    Top payoff: {top_payoff}")
    
    return patterns


if __name__ == '__main__':
    # Test with a sample video
    test_url = "https://www.youtube.com/shorts/s600FYgI5-s"
    print(f"Testing Gemini analyzer with: {test_url}")
    
    result = analyze_youtube_video(test_url)
    if result:
        print("\n--- Full Analysis Result ---")
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed!")

