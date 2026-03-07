# youtube_agent_system/intelligence_agent.py
"""
Intelligence Agent - The Brain of the Autonomous Content Engine

This agent is responsible for:
1. Collecting and analyzing rival content using Gemini
2. Learning patterns from successful content
3. Making data-driven content recommendations
4. Adapting strategy based on our channel's performance

This agent does NOT create videos - it only provides intelligence
to the Strategy Agent for content decisions.
"""

import json
from . import config
from . import knowledge_base
from .tools import rival_scanner, transcript_analyzer, gemini_analyzer


class IntelligenceAgent:
    """
    The brain of the autonomous content engine.
    
    Orchestrates learning from rival content and our own performance
    to make intelligent content decisions.
    """
    
    def __init__(self):
        self.rival_channels = config.RIVAL_CHANNEL_URLS
        self.videos_per_channel = config.RIVAL_SCAN_VIDEOS_PER_CHANNEL
        print("--- [BRAIN] Intelligence Agent Initialized ---")
    
    def scan_and_analyze_rivals(self, force_rescan: bool = False) -> dict:
        """
        Scans rival channels and deeply analyzes their content with Gemini.
        
        This is the main learning function that populates the knowledge base
        with content patterns from successful rival videos.
        
        Args:
            force_rescan: If True, re-analyze videos even if already in database.
            
        Returns:
            Summary of what was learned.
        """
        print("--- [SCAN] Intelligence Agent: Starting Rival Content Analysis ---")
        
        all_video_urls = []
        
        # Step 1: Gather video URLs from all rival channels
        for channel_url in self.rival_channels:
            print(f"--- Scanning channel: {channel_url} ---")
            videos = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=self.videos_per_channel)
            
            if videos:
                # Get actual video URLs from the titles (need to construct them)
                # Note: rival_scanner returns titles/views, not URLs, so we need video IDs
                # For now, we'll use the channel's shorts tab directly
                channel_shorts_url = f"{channel_url}/shorts"
                all_video_urls.append(channel_shorts_url)
                print(f"  Found {len(videos)} videos from this channel")
        
        # Step 2: Analyze videos with Gemini
        # Note: We'll analyze the shorts directly via URL
        analyzed_count = 0
        new_analyses = []
        
        # Get individual video URLs by scanning the channel
        for channel_url in self.rival_channels:
            print(f"--- Deep analyzing videos from: {channel_url} ---")
            
            # Get video info including URLs
            videos_info = self._get_video_urls_from_channel(channel_url)
            
            for video_info in videos_info[:self.videos_per_channel]:
                video_url = video_info.get('url')
                video_id = video_info.get('id', video_url)
                
                if not video_url:
                    continue
                
                # Check if already analyzed (unless force rescan)
                if not force_rescan:
                    existing = knowledge_base.get_all_rival_analyses()
                    already_analyzed = any(a.get('video_url') == video_url for a in existing)
                    if already_analyzed:
                        print(f"  Skipping (already analyzed): {video_url}")
                        continue
                
                # Analyze with Groq (transcript-based) - FREE and no rate limits!
                print(f"  Analyzing: {video_url}")
                analysis = transcript_analyzer.analyze_youtube_video(video_url)
                
                if analysis:
                    # Save to knowledge base
                    knowledge_base.save_rival_analysis(
                        video_id=video_id,
                        video_url=video_url,
                        analysis_data=analysis,
                        metadata={
                            'channel': channel_url,
                            'views': video_info.get('views', 0),
                            'title': video_info.get('title', '')
                        }
                    )
                    new_analyses.append(analysis)
                    analyzed_count += 1
        
        # Step 3: Synthesize patterns from all analyses
        if new_analyses:
            print(f"--- [DNA] Synthesizing patterns from {analyzed_count} new analyses ---")
            all_analyses = knowledge_base.get_all_rival_analyses()
            
            # Get full analysis data for pattern extraction
            full_analyses = [a.get('full_analysis', {}) for a in all_analyses if a.get('full_analysis')]
            
            if full_analyses:
                # Use local pattern extraction (works with both Gemini and Groq analyses)
                patterns = self._extract_patterns_locally(full_analyses)
                knowledge_base.save_synthesized_patterns(patterns)
                print("--- [OK] Pattern synthesis complete ---")
        
        summary = {
            'channels_scanned': len(self.rival_channels),
            'new_videos_analyzed': analyzed_count,
            'total_videos_in_db': knowledge_base.get_rival_count(),
            'patterns_updated': len(new_analyses) > 0
        }
        
        print(f"--- [STATS] Rival Analysis Complete: {summary} ---")
        return summary
    
    def _extract_patterns_locally(self, analyses: list[dict]) -> dict:
        """
        Extracts patterns from analyses locally (no API call needed).
        Works with both Gemini and Groq analysis outputs.
        """
        if not analyses:
            return {"error": "No analyses provided"}
        
        print(f"--- [DNA] Extracting patterns from {len(analyses)} video analyses ---")
        
        # Aggregate data
        hook_techniques = {}
        content_categories = {}
        payoff_types = {}
        emotions = {}
        high_performers = []
        example_hooks = []
        
        for analysis in analyses:
            # Count hook techniques
            hook_tech = analysis.get('hook', {}).get('technique', 'unknown')
            hook_techniques[hook_tech] = hook_techniques.get(hook_tech, 0) + 1
            
            # Collect hook examples
            hook_text = analysis.get('hook', {}).get('text', '')
            if hook_text and len(example_hooks) < 5:
                example_hooks.append(hook_text)
            
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
            view_appeal = analysis.get('estimated_view_appeal', 0) or 0
            if view_appeal >= 7:
                high_performers.append(analysis)
        
        # Sort by frequency
        top_hook = max(hook_techniques, key=hook_techniques.get) if hook_techniques else "unknown"
        top_category = max(content_categories, key=content_categories.get) if content_categories else "OTHER"
        top_payoff = max(payoff_types, key=payoff_types.get) if payoff_types else "unknown"
        top_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
        
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
                "example_hooks_to_emulate": example_hooks[:3]
            }
        }
        
        print(f"--- [TARGET] Pattern extraction complete ---")
        print(f"    Top category: {top_category}")
        print(f"    Top hook technique: {top_hook}")
        print(f"    Top payoff: {top_payoff}")
        
        return patterns
    
    def _get_video_urls_from_channel(self, channel_url: str) -> list[dict]:
        """
        Gets video URLs and metadata from a channel.
        
        Returns list of dicts with 'url', 'id', 'title', 'views' keys.
        """
        import yt_dlp
        
        # Try shorts first, then fall back to videos
        urls_to_try = [
            f"{channel_url}/shorts",
            f"{channel_url}/videos"
        ]
        
        ydl_opts = {
            'playlistend': self.videos_per_channel,
            'extract_flat': True,  # Use flat mode to avoid format errors
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }
        
        for url in urls_to_try:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info and 'entries' in info and info['entries']:
                        videos = []
                        for entry in info['entries']:
                            if entry and entry.get('id'):
                                video_id = entry.get('id', '')
                                videos.append({
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'id': video_id,
                                    'title': entry.get('title', ''),
                                    'views': entry.get('view_count', 0) or 0
                                })
                        if videos:
                            print(f"  Got {len(videos)} video URLs from {url}")
                            return videos
            except Exception as e:
                # Try next URL
                continue
        
        print(f"  Could not get video URLs from {channel_url}")
        return []
    
    def get_content_recommendation(self) -> dict:
        """
        Returns a data-driven content recommendation.
        
        This is the main interface for the Strategy Agent.
        Combines learned patterns with our performance data.
        
        Returns:
            Dictionary with content recommendation and confidence.
        """
        print("--- [TARGET] Intelligence Agent: Generating Content Recommendation ---")
        
        # Get base recommendation from patterns
        recommendation = knowledge_base.get_content_recommendation()
        
        if recommendation.get('use_fallback'):
            print("  No patterns available. Recommending exploration mode.")
            return {
                'mode': 'explore',
                'message': 'No learned patterns yet. Using diverse content strategy.',
                'content_category': 'AITA',  # Safe default
                'hook_style': 'shocking revelation',
                'payoff_type': 'justice served',
                'confidence': 0.3,
                'example_hooks': []
            }
        
        # Enhance with performance correlation from our videos
        performance_data = knowledge_base.get_pattern_performance_correlation()
        
        # Adjust recommendation based on what has worked for us
        if performance_data:
            # Find our best performing pattern
            best_pattern = None
            best_score = 0
            for pattern, stats in performance_data.items():
                if stats.get('avg_score', 0) > best_score and stats.get('count', 0) >= 2:
                    best_score = stats['avg_score']
                    best_pattern = pattern
            
            if best_pattern:
                recommendation['our_best_pattern'] = best_pattern
                recommendation['our_best_score'] = best_score
        
        recommendation['mode'] = 'learned'
        print(f"  Recommendation: {recommendation.get('content_category')} with {recommendation.get('hook_style')}")
        print(f"  Confidence: {recommendation.get('confidence', 0):.0%}")
        
        return recommendation
    
    def should_experiment(self) -> bool:
        """
        Determines if we should try experimental content.
        
        Based on recent performance, decides if we should deviate
        from proven patterns to explore new content types.
        
        Returns:
            True if we should experiment, False to stick with learned patterns.
        """
        # Get recent performance
        all_insights = knowledge_base.get_all_insights_with_metadata()
        
        if len(all_insights) < 5:
            # Not enough data, experiment
            return True
        
        # Look at last 5 videos
        recent = all_insights[-5:]
        
        # Calculate average performance
        total_score = 0
        for insight in recent:
            views = insight.get('metadata', {}).get('views', 0)
            likes = insight.get('metadata', {}).get('likes', 0)
            total_score += views + (likes * 10)
        
        avg_score = total_score / len(recent)
        
        # If performance is declining, experiment
        # Compare to earlier videos
        if len(all_insights) >= 10:
            earlier = all_insights[-10:-5]
            earlier_total = 0
            for insight in earlier:
                views = insight.get('metadata', {}).get('views', 0)
                likes = insight.get('metadata', {}).get('likes', 0)
                earlier_total += views + (likes * 10)
            
            earlier_avg = earlier_total / len(earlier)
            
            if avg_score < earlier_avg * 0.7:  # 30% decline
                print("--- [DOWN] Performance declining. Recommending experimentation. ---")
                return True
        
        return False
    
    def get_status_report(self) -> dict:
        """
        Returns a comprehensive status report of the intelligence system.
        """
        stats = knowledge_base.get_knowledge_base_stats()
        recommendation = self.get_content_recommendation()
        
        return {
            'knowledge_base': stats,
            'current_recommendation': recommendation,
            'should_experiment': self.should_experiment(),
            'system_status': 'ready' if stats['rival_videos_analyzed'] > 0 else 'needs_training'
        }


def run_learning_cycle():
    """
    Runs a complete learning cycle.
    
    Call this periodically to:
    1. Scan rival channels for new content
    2. Analyze new videos with Gemini
    3. Update pattern library
    4. Generate new recommendations
    """
    agent = IntelligenceAgent()
    
    print("=== [BRAIN] INTELLIGENCE AGENT: LEARNING CYCLE START ===")
    
    # Scan and analyze rivals
    scan_result = agent.scan_and_analyze_rivals()
    
    # Get updated recommendation
    recommendation = agent.get_content_recommendation()
    
    # Status report
    status = agent.get_status_report()
    
    print("=== [BRAIN] LEARNING CYCLE COMPLETE ===")
    print(f"Status: {status['system_status']}")
    print(f"Videos analyzed: {status['knowledge_base']['rival_videos_analyzed']}")
    print(f"Recommendation confidence: {recommendation.get('confidence', 0):.0%}")
    
    return status


if __name__ == '__main__':
    # Test the intelligence agent
    print("--- Testing Intelligence Agent ---")
    
    agent = IntelligenceAgent()
    
    # Get status
    status = agent.get_status_report()
    print(f"\nStatus Report:")
    print(json.dumps(status, indent=2, default=str))
    
    # Get recommendation
    print("\n--- Content Recommendation ---")
    rec = agent.get_content_recommendation()
    print(json.dumps(rec, indent=2))

