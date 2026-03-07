# youtube_agent_system/autonomous_runner.py
"""
Autonomous Content Research & Production Engine

This is the main autonomous system that:
1. Continuously researches Reddit and YouTube for viral content
2. Discovers what niches sell best
3. Learns from competitor success
4. Produces and uploads videos automatically
5. Checkpoints progress every 30 minutes for recovery
6. Can run for hours or days autonomously

Usage:
    python -m youtube_agent_system.autonomous_runner
    python -m youtube_agent_system.autonomous_runner --duration 24  # Run for 24 hours
    python -m youtube_agent_system.autonomous_runner --test-mode    # Quick test
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
import traceback

from . import config
from . import knowledge_base
from . import intelligence_agent
from . import main as pipeline
from .tools import youtube_searcher, reddit_scraper, transcript_analyzer


# ============================================================
# CONFIGURATION
# ============================================================

CHECKPOINT_DIR = os.path.join(config.BASE_DIR, "checkpoints")
CHECKPOINT_FILE = os.path.join(CHECKPOINT_DIR, "checkpoint_latest.json")
LOG_DIR = config.LOGS_DIR

# Ensure directories exist
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# ============================================================
# AUTONOMOUS RUNNER CLASS
# ============================================================

class AutonomousRunner:
    """
    The main autonomous research and production engine.
    
    Runs continuously, learning and producing content while
    maintaining checkpoints for recovery.
    """
    
    def __init__(
        self,
        checkpoint_interval_minutes: int = 30,
        videos_per_cycle: int = 1,
        research_before_produce: bool = True
    ):
        """
        Initialize the autonomous runner.
        
        Args:
            checkpoint_interval_minutes: How often to save progress
            videos_per_cycle: How many videos to produce per research cycle
            research_before_produce: If True, research before each video
        """
        self.checkpoint_interval = checkpoint_interval_minutes * 60  # Convert to seconds
        self.videos_per_cycle = videos_per_cycle
        self.research_before_produce = research_before_produce
        
        # Runtime state
        self.start_time = None
        self.last_checkpoint_time = None
        self.stop_requested = False
        
        # Progress tracking
        self.stats = {
            'run_started': None,
            'total_runtime_seconds': 0,
            'cycles_completed': 0,
            
            # Research stats
            'reddit_stories_collected': 0,
            'youtube_videos_analyzed': 0,
            'advice_videos_analyzed': 0,
            'competitors_discovered': 0,
            'niches_researched': 0,
            
            # Production stats
            'videos_produced': 0,
            'videos_uploaded': 0,
            'upload_failures': 0,
            
            # Learning stats
            'patterns_updated': 0,
            'knowledge_base_entries': 0,
            
            # Current cycle info
            'current_phase': 'initializing',
            'last_error': None,
            'last_checkpoint': None,
        }
        
        # Log file for this run
        self.log_file = os.path.join(
            LOG_DIR,
            f"autonomous_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║      🤖 AUTONOMOUS CONTENT ENGINE INITIALIZED 🤖              ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        self._log("Autonomous Runner initialized")
    
    def _log(self, message: str, level: str = "INFO"):
        """Logs a message to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def _log_progress(self):
        """Logs current progress statistics."""
        self._log("=" * 60)
        self._log("📊 PROGRESS REPORT")
        self._log("=" * 60)
        
        runtime = self.stats['total_runtime_seconds']
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        
        self._log(f"⏱️  Runtime: {hours}h {minutes}m")
        self._log(f"🔄 Cycles completed: {self.stats['cycles_completed']}")
        self._log(f"📕 Reddit stories: {self.stats['reddit_stories_collected']}")
        self._log(f"📺 YouTube videos analyzed: {self.stats['youtube_videos_analyzed']}")
        self._log(f"📚 Advice videos learned: {self.stats['advice_videos_analyzed']}")
        self._log(f"🎯 Competitors found: {self.stats['competitors_discovered']}")
        self._log(f"📈 Niches researched: {self.stats['niches_researched']}")
        self._log(f"🎬 Videos produced: {self.stats['videos_produced']}")
        self._log(f"🚀 Videos uploaded: {self.stats['videos_uploaded']}")
        self._log(f"🧠 Patterns updated: {self.stats['patterns_updated']}")
        self._log(f"💾 Knowledge base entries: {self.stats['knowledge_base_entries']}")
        self._log(f"🔖 Current phase: {self.stats['current_phase']}")
        self._log("=" * 60)
    
    def checkpoint(self) -> bool:
        """
        Saves current progress to disk for recovery.
        
        Returns:
            True if checkpoint saved successfully
        """
        self._log("💾 Saving checkpoint...")
        
        checkpoint_data = {
            'stats': self.stats.copy(),
            'checkpoint_time': datetime.now().isoformat(),
            'log_file': self.log_file,
        }
        
        checkpoint_data['stats']['total_runtime_seconds'] = int(
            (datetime.now() - self.start_time).total_seconds()
        ) if self.start_time else 0
        
        checkpoint_data['stats']['last_checkpoint'] = datetime.now().isoformat()
        
        try:
            # Save latest checkpoint
            with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            
            # Also save timestamped backup
            backup_file = os.path.join(
                CHECKPOINT_DIR,
                f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            
            self.last_checkpoint_time = datetime.now()
            self.stats['last_checkpoint'] = self.last_checkpoint_time.isoformat()
            
            # Log detailed progress
            self._log_progress()
            
            self._log(f"✅ Checkpoint saved: {CHECKPOINT_FILE}")
            return True
            
        except Exception as e:
            self._log(f"❌ Checkpoint failed: {e}", "ERROR")
            return False
    
    def recover_from_checkpoint(self) -> bool:
        """
        Attempts to recover from the last checkpoint.
        
        Returns:
            True if recovery successful
        """
        self._log("🔄 Attempting to recover from checkpoint...")
        
        if not os.path.exists(CHECKPOINT_FILE):
            self._log("No checkpoint file found - starting fresh")
            return False
        
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            self.stats = checkpoint_data.get('stats', self.stats)
            
            checkpoint_time = checkpoint_data.get('checkpoint_time', 'Unknown')
            self._log(f"✅ Recovered from checkpoint: {checkpoint_time}")
            self._log(f"   Cycles completed: {self.stats['cycles_completed']}")
            self._log(f"   Videos uploaded: {self.stats['videos_uploaded']}")
            
            return True
            
        except Exception as e:
            self._log(f"❌ Recovery failed: {e}", "ERROR")
            return False
    
    def _research_phase(self) -> dict:
        """
        Executes the research phase:
        1. Scrape Reddit for new stories
        2. Search YouTube for advice videos
        3. Discover competitors
        4. Analyze niche potential
        5. Learn from transcripts
        
        Returns:
            Summary of what was researched
        """
        self._log("🔍 STARTING RESEARCH PHASE")
        self.stats['current_phase'] = 'research'
        
        results = {
            'reddit_stories': 0,
            'youtube_analyzed': 0,
            'advice_learned': 0,
            'competitors': 0,
            'niches': 0,
        }
        
        # --- 1. Reddit Stories ---
        self._log("📕 Phase 1: Collecting Reddit stories...")
        try:
            reddit_status = reddit_scraper.check_reddit_availability()
            if reddit_status['available']:
                stories = reddit_scraper.scrape_all_subreddits(
                    time_filter="week",
                    limit_per_sub=20,
                    min_score=200
                )
                
                # Save to knowledge base
                for story in stories[:50]:  # Limit to top 50
                    try:
                        knowledge_base.save_reddit_story(
                            story_id=story['id'],
                            story_data=story,
                            metadata={
                                'subreddit': story['subreddit'],
                                'category': story['category'],
                                'viral_score': story['viral_score']
                            }
                        )
                        results['reddit_stories'] += 1
                    except Exception as e:
                        pass  # Knowledge base may not have this function yet
                
                self.stats['reddit_stories_collected'] += results['reddit_stories']
                self._log(f"   Collected {results['reddit_stories']} stories")
            else:
                self._log(f"   Reddit not available: {reddit_status['message']}")
        except Exception as e:
            self._log(f"   Reddit error: {e}", "ERROR")
        
        # --- 2. YouTube Advice Videos ---
        self._log("📚 Phase 2: Learning from YouTube advice videos...")
        try:
            advice_videos = youtube_searcher.get_growth_advice_videos(max_per_query=3)
            
            for video in advice_videos[:10]:  # Analyze top 10
                try:
                    analysis = transcript_analyzer.analyze_youtube_video(video['url'])
                    if analysis:
                        # Save insights
                        knowledge_base.save_tutorial_insight(
                            video_id=video['id'],
                            insights={
                                'title': video['title'],
                                'views': video['views'],
                                'query': video.get('advice_query', ''),
                                'analysis': analysis
                            }
                        )
                        results['advice_learned'] += 1
                        self.stats['advice_videos_analyzed'] += 1
                except Exception as e:
                    pass  # Continue with next video
            
            self._log(f"   Learned from {results['advice_learned']} advice videos")
        except Exception as e:
            self._log(f"   Advice video error: {e}", "ERROR")
        
        # --- 3. Discover Competitors ---
        self._log("🎯 Phase 3: Discovering competitors...")
        try:
            all_channels = []
            for niche in ['AITA', 'REVENGE', 'RELATIONSHIP']:
                channels = youtube_searcher.discover_competitor_channels(niche)
                all_channels.extend(channels)
            
            results['competitors'] = len(set(c['url'] for c in all_channels))
            self.stats['competitors_discovered'] += results['competitors']
            self._log(f"   Discovered {results['competitors']} competitor channels")
        except Exception as e:
            self._log(f"   Competitor discovery error: {e}", "ERROR")
        
        # --- 4. Analyze Niches ---
        self._log("📈 Phase 4: Analyzing niche potential...")
        try:
            niche_analyses = youtube_searcher.discover_all_niche_potentials()
            results['niches'] = len(niche_analyses)
            self.stats['niches_researched'] = results['niches']
            
            if niche_analyses:
                best_niche = niche_analyses[0]
                self._log(f"   Best niche: {best_niche['niche']} (score: {best_niche['potential_score']})")
        except Exception as e:
            self._log(f"   Niche analysis error: {e}", "ERROR")
        
        # --- 5. Analyze Competitor Videos (Extended) ---
        self._log("🎥 Phase 5: Deep analyzing competitor videos...")
        try:
            ia = intelligence_agent.IntelligenceAgent()
            scan_result = ia.scan_and_analyze_rivals(force_rescan=False)
            results['youtube_analyzed'] = scan_result.get('new_videos_analyzed', 0)
            self.stats['youtube_videos_analyzed'] += results['youtube_analyzed']
            self._log(f"   Analyzed {results['youtube_analyzed']} competitor videos")
        except Exception as e:
            self._log(f"   Competitor analysis error: {e}", "ERROR")
        
        # Update knowledge base stats
        try:
            kb_stats = knowledge_base.get_knowledge_base_stats()
            self.stats['knowledge_base_entries'] = (
                kb_stats.get('rival_videos_analyzed', 0) +
                kb_stats.get('our_videos_analyzed', 0)
            )
        except:
            pass
        
        self._log(f"✅ Research phase complete: {results}")
        return results
    
    def _production_phase(self) -> dict:
        """
        Executes the production phase:
        1. Generate optimized content using learned patterns
        2. Produce video
        3. Upload to YouTube
        
        Returns:
            Summary of what was produced
        """
        self._log("🎬 STARTING PRODUCTION PHASE")
        self.stats['current_phase'] = 'production'
        
        results = {
            'videos_produced': 0,
            'videos_uploaded': 0,
            'errors': []
        }
        
        for i in range(self.videos_per_cycle):
            self._log(f"📹 Producing video {i+1}/{self.videos_per_cycle}...")
            
            try:
                # Run the intelligent pipeline
                result = pipeline.run_intelligent_pipeline(skip_learning=True)
                
                if result and result.get('video_id'):
                    results['videos_produced'] += 1
                    results['videos_uploaded'] += 1
                    self.stats['videos_produced'] += 1
                    self.stats['videos_uploaded'] += 1
                    self._log(f"   ✅ Video uploaded: {result.get('title', 'Unknown')[:50]}...")
                else:
                    results['errors'].append("Pipeline returned no video ID")
                    self.stats['upload_failures'] += 1
                    self._log("   ❌ Video production failed")
                    
            except Exception as e:
                error_msg = str(e)
                results['errors'].append(error_msg)
                self.stats['upload_failures'] += 1
                self.stats['last_error'] = error_msg
                self._log(f"   ❌ Error: {error_msg}", "ERROR")
        
        self._log(f"✅ Production phase complete: {results['videos_uploaded']}/{self.videos_per_cycle} uploaded")
        return results
    
    def _should_checkpoint(self) -> bool:
        """Returns True if it's time to save a checkpoint."""
        if self.last_checkpoint_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_checkpoint_time).total_seconds()
        return elapsed >= self.checkpoint_interval
    
    def run(
        self,
        max_runtime_hours: float = 24,
        continuous: bool = True,
        cycle_delay_minutes: int = 5
    ):
        """
        Main run loop for the autonomous engine.
        
        Args:
            max_runtime_hours: Maximum time to run
            continuous: If True, keep running until max_runtime
            cycle_delay_minutes: Delay between production cycles
        """
        self.start_time = datetime.now()
        self.stats['run_started'] = self.start_time.isoformat()
        max_runtime_seconds = max_runtime_hours * 3600
        
        self._log("╔════════════════════════════════════════════════════════════════╗")
        self._log("║           🚀 AUTONOMOUS ENGINE STARTING 🚀                    ║")
        self._log("╚════════════════════════════════════════════════════════════════╝")
        self._log(f"Max runtime: {max_runtime_hours} hours")
        self._log(f"Checkpoint interval: {self.checkpoint_interval // 60} minutes")
        self._log(f"Videos per cycle: {self.videos_per_cycle}")
        
        try:
            while not self.stop_requested:
                cycle_start = datetime.now()
                self.stats['cycles_completed'] += 1
                cycle_num = self.stats['cycles_completed']
                
                self._log(f"\n{'='*60}")
                self._log(f"🔄 STARTING CYCLE #{cycle_num}")
                self._log(f"{'='*60}")
                
                # Check runtime
                runtime = (datetime.now() - self.start_time).total_seconds()
                self.stats['total_runtime_seconds'] = int(runtime)
                
                if runtime >= max_runtime_seconds:
                    self._log(f"⏰ Max runtime reached ({max_runtime_hours}h)")
                    break
                
                # --- RESEARCH PHASE ---
                if self.research_before_produce:
                    try:
                        self._research_phase()
                    except Exception as e:
                        self._log(f"Research phase error: {e}", "ERROR")
                        traceback.print_exc()
                
                # --- PRODUCTION PHASE ---
                try:
                    self._production_phase()
                except Exception as e:
                    self._log(f"Production phase error: {e}", "ERROR")
                    traceback.print_exc()
                
                # --- CHECKPOINT ---
                if self._should_checkpoint():
                    self.checkpoint()
                
                # --- UPDATE PATTERNS ---
                self.stats['current_phase'] = 'pattern_update'
                try:
                    ia = intelligence_agent.IntelligenceAgent()
                    status = ia.get_status_report()
                    if status.get('knowledge_base', {}).get('patterns_saved', 0) > 0:
                        self.stats['patterns_updated'] = status['knowledge_base']['patterns_saved']
                except Exception as e:
                    pass
                
                # --- CHECK IF SHOULD CONTINUE ---
                if not continuous:
                    self._log("Single cycle mode - stopping")
                    break
                
                # --- DELAY BEFORE NEXT CYCLE ---
                self.stats['current_phase'] = 'waiting'
                self._log(f"⏳ Waiting {cycle_delay_minutes} minutes before next cycle...")
                
                for _ in range(cycle_delay_minutes * 60):
                    if self.stop_requested:
                        break
                    time.sleep(1)
                    
                    # Check for checkpoint during wait
                    if self._should_checkpoint():
                        self.checkpoint()
        
        except KeyboardInterrupt:
            self._log("⚠️ Interrupted by user (Ctrl+C)")
        except Exception as e:
            self._log(f"❌ Fatal error: {e}", "ERROR")
            traceback.print_exc()
        finally:
            # Final checkpoint
            self.checkpoint()
            
            self._log("╔════════════════════════════════════════════════════════════════╗")
            self._log("║           🏁 AUTONOMOUS ENGINE STOPPED 🏁                     ║")
            self._log("╚════════════════════════════════════════════════════════════════╝")
            self._log_progress()
    
    def stop(self):
        """Gracefully stops the runner."""
        self._log("⚠️ Stop requested...")
        self.stop_requested = True
    
    def get_progress_report(self) -> dict:
        """Returns the current progress statistics."""
        report = self.stats.copy()
        
        if self.start_time:
            report['total_runtime_seconds'] = int(
                (datetime.now() - self.start_time).total_seconds()
            )
        
        return report


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    """Command-line interface for the autonomous runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Autonomous YouTube Content Research & Production Engine"
    )
    parser.add_argument(
        '--duration', type=float, default=24,
        help='Maximum runtime in hours (default: 24)'
    )
    parser.add_argument(
        '--checkpoint-interval', type=int, default=30,
        help='Checkpoint interval in minutes (default: 30)'
    )
    parser.add_argument(
        '--videos-per-cycle', type=int, default=1,
        help='Videos to produce per cycle (default: 1)'
    )
    parser.add_argument(
        '--cycle-delay', type=int, default=5,
        help='Delay between cycles in minutes (default: 5)'
    )
    parser.add_argument(
        '--test-mode', action='store_true',
        help='Quick test mode (1 cycle, no delay)'
    )
    parser.add_argument(
        '--recover', action='store_true',
        help='Recover from last checkpoint'
    )
    parser.add_argument(
        '--research-only', action='store_true',
        help='Only do research, no video production'
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = AutonomousRunner(
        checkpoint_interval_minutes=args.checkpoint_interval,
        videos_per_cycle=args.videos_per_cycle,
        research_before_produce=True
    )
    
    # Handle recovery
    if args.recover:
        runner.recover_from_checkpoint()
    
    # Handle test mode
    if args.test_mode:
        print("\n🧪 TEST MODE: Running single cycle...")
        runner.run(
            max_runtime_hours=1,
            continuous=False,
            cycle_delay_minutes=0
        )
    elif args.research_only:
        print("\n🔍 RESEARCH ONLY MODE...")
        runner._research_phase()
        runner.checkpoint()
    else:
        # Normal run
        runner.run(
            max_runtime_hours=args.duration,
            continuous=True,
            cycle_delay_minutes=args.cycle_delay
        )


if __name__ == '__main__':
    main()
