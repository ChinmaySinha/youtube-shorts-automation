# youtube_agent_system/tools/transcript_analyzer.py
"""
Transcript-Based Video Analyzer

Uses yt-dlp to extract YouTube video transcripts (FREE, no API needed)
and Groq to analyze the content patterns.

This is the PRIMARY method for learning from rival content.
No rate limits, completely free!
"""

import json
import re
import subprocess
import tempfile
import os
from groq import Groq
from .. import config


def get_video_transcript(video_url: str) -> dict | None:
    """
    Extracts transcript/subtitles from a YouTube video using yt-dlp Python API.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        Dictionary with 'transcript', 'title', 'duration', 'views' or None if failed.
    """
    print(f"--- [TRANSCRIPT] Extracting transcript from {video_url} ---")
    
    try:
        import yt_dlp
        
        # Create temp directory for subtitle files
        with tempfile.TemporaryDirectory() as tmpdir:
            
            # Options for extracting subtitles
            ydl_opts = {
                'writeautomaticsub': True,
                'writesubtitles': True,
                'subtitleslangs': ['en', 'en-US', 'en-GB'],
                'subtitlesformat': 'vtt',
                'skip_download': True,
                'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
            
            video_info = None
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    video_info = ydl.extract_info(video_url, download=True)
                except Exception as e:
                    print(f"  yt-dlp extract error: {e}")
                    return None
            
            if not video_info:
                print(f"  Could not extract video info")
                return None
            
            title = video_info.get('title', '')
            duration = video_info.get('duration', 0)
            views = video_info.get('view_count', 0)
            video_id = video_info.get('id', '')
            
            # Look for VTT files in temp directory
            transcript_text = ""
            for file in os.listdir(tmpdir):
                if file.endswith('.vtt') and video_id in file:
                    vtt_path = os.path.join(tmpdir, file)
                    transcript_text = _parse_vtt_file(vtt_path)
                    if transcript_text:
                        break
            
            # If no VTT file, try to get from automatic_captions in video_info
            if not transcript_text:
                auto_caps = video_info.get('automatic_captions', {})
                subtitles = video_info.get('subtitles', {})
                
                # Try to download captions directly
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in auto_caps:
                        for fmt in auto_caps[lang]:
                            if fmt.get('ext') == 'vtt' or 'vtt' in fmt.get('url', ''):
                                try:
                                    import urllib.request
                                    vtt_url = fmt.get('url')
                                    if vtt_url:
                                        vtt_content = urllib.request.urlopen(vtt_url, timeout=30).read().decode('utf-8')
                                        transcript_text = _parse_vtt_content(vtt_content)
                                        if transcript_text:
                                            break
                                except:
                                    continue
                        if transcript_text:
                            break
                    
                    if not transcript_text and lang in subtitles:
                        for fmt in subtitles[lang]:
                            if fmt.get('ext') == 'vtt' or 'vtt' in fmt.get('url', ''):
                                try:
                                    import urllib.request
                                    vtt_url = fmt.get('url')
                                    if vtt_url:
                                        vtt_content = urllib.request.urlopen(vtt_url, timeout=30).read().decode('utf-8')
                                        transcript_text = _parse_vtt_content(vtt_content)
                                        if transcript_text:
                                            break
                                except:
                                    continue
                        if transcript_text:
                            break
            
            if not transcript_text:
                print(f"  No transcript available for {video_url}")
                return None
            
            print(f"  Transcript extracted: {len(transcript_text)} characters")
            
            return {
                'transcript': transcript_text,
                'title': title,
                'duration': duration,
                'views': views,
                'video_url': video_url
            }
            
    except Exception as e:
        print(f"  Error extracting transcript: {e}")
        import traceback
        traceback.print_exc()
        return None


def _parse_vtt_content(content: str) -> str:
    """
    Parses VTT content string and extracts clean text.
    """
    lines = content.split('\n')
    text_lines = []
    
    for line in lines:
        # Skip timestamps, WEBVTT header, and empty lines
        if '-->' in line:
            continue
        if line.strip().startswith('WEBVTT'):
            continue
        if line.strip().startswith('Kind:'):
            continue
        if line.strip().startswith('Language:'):
            continue
        if re.match(r'^\d+$', line.strip()):
            continue
        if not line.strip():
            continue
        
        # Clean HTML tags
        clean_line = re.sub(r'<[^>]+>', '', line)
        clean_line = re.sub(r'\[.*?\]', '', clean_line)
        
        if clean_line.strip():
            text_lines.append(clean_line.strip())
    
    # Remove duplicates while maintaining order
    seen = set()
    unique_lines = []
    for line in text_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
    
    return ' '.join(unique_lines)


def _parse_vtt_file(vtt_path: str) -> str:
    """
    Parses a VTT subtitle file and extracts clean text.
    """
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove VTT header
        lines = content.split('\n')
        text_lines = []
        
        for line in lines:
            # Skip timestamps, WEBVTT header, and empty lines
            if '-->' in line:
                continue
            if line.strip().startswith('WEBVTT'):
                continue
            if line.strip().startswith('Kind:'):
                continue
            if line.strip().startswith('Language:'):
                continue
            if re.match(r'^\d+$', line.strip()):
                continue
            if not line.strip():
                continue
            
            # Clean HTML tags
            clean_line = re.sub(r'<[^>]+>', '', line)
            # Remove positioning tags like <c>
            clean_line = re.sub(r'\[.*?\]', '', clean_line)
            
            if clean_line.strip():
                text_lines.append(clean_line.strip())
        
        # Remove duplicates while maintaining order (VTT often has overlapping lines)
        seen = set()
        unique_lines = []
        for line in text_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return ' '.join(unique_lines)
        
    except Exception as e:
        print(f"  Error parsing VTT file: {e}")
        return ""


# Groq analysis prompt - similar to Gemini but for text-only analysis
# NOTE: Double curly braces {{ }} are used to escape them for Python .format()
TRANSCRIPT_ANALYSIS_PROMPT = """
You are an expert content analyst specializing in viral YouTube Shorts, particularly Reddit story content (AITA, Revenge stories, Relationship drama, etc.).

Analyze this YouTube video TRANSCRIPT and extract the following information in a structured JSON format:

{{
    "transcript": "Copy of the transcript provided",
    
    "hook": {{
        "text": "The exact first 1-2 sentences that hook the viewer",
        "technique": "Name the hook technique (e.g., 'shocking revelation', 'mystery question', 'controversial statement', 'emotional trauma')",
        "rating": 1-10
    }},
    
    "story_structure": {{
        "setup": "Brief description of the situation/context",
        "conflict": "What's the main problem/drama?",
        "twist": "Any unexpected turn? (null if none)",
        "resolution": "How does it end?",
        "payoff_type": "Type of ending (e.g., 'revenge satisfied', 'justice served', 'wholesome', 'cliffhanger', 'validation')"
    }},
    
    "emotional_arc": {{
        "starting_emotion": "What emotion does the story start with?",
        "peak_emotion": "What's the strongest emotion triggered?",
        "ending_emotion": "What emotion is the viewer left with?",
        "emotion_journey": ["list", "of", "emotions", "in", "order"]
    }},
    
    "content_category": "One of: AITA, REVENGE, RELATIONSHIP, FAMILY_DRAMA, WORKPLACE, KARMA, WHOLESOME, MYSTERY, OTHER",
    
    "pacing": {{
        "words_per_minute_estimate": "fast/medium/slow",
        "dramatic_pauses": true/false,
        "sentence_length": "short/medium/long"
    }},
    
    "engagement_triggers": [
        "List specific moments designed to keep viewers watching",
        "e.g., 'cliffhanger mid-story', 'shocking reveal', 'emotional payoff'"
    ],
    
    "what_makes_it_work": "1-2 sentences explaining why this video is engaging",
    
    "estimated_view_appeal": 1-10
}}

Here is the transcript to analyze:
---
VIDEO TITLE: {title}
VIEWS: {views}
DURATION: {duration} seconds

TRANSCRIPT:
{transcript}
---

Be precise with your analysis. If you can't determine something, use null instead of guessing.
Return ONLY valid JSON, no other text.
"""


def analyze_transcript_with_groq(transcript_data: dict) -> dict | None:
    """
    Analyzes a video transcript using Groq's LLM.
    
    Args:
        transcript_data: Dictionary from get_video_transcript()
        
    Returns:
        Analysis dictionary or None if failed.
    """
    print(f"--- [GROQ] Analyzing transcript with Groq ---")
    
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        
        # Build the prompt
        prompt = TRANSCRIPT_ANALYSIS_PROMPT.format(
            title=transcript_data.get('title', 'Unknown'),
            views=transcript_data.get('views', 0),
            duration=transcript_data.get('duration', 0),
            transcript=transcript_data.get('transcript', '')[:8000]  # Limit transcript length
        )
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert content analyst. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        # Find the JSON object in the response (it should start with { and end with })
        json_start = response_text.find('{')
        json_end = response_text.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            response_text = response_text[json_start:json_end + 1]
        
        analysis = json.loads(response_text)
        
        print(f"--- [OK] Groq analysis complete ---")
        print(f"    Category: {analysis.get('content_category', 'Unknown')}")
        print(f"    Hook technique: {analysis.get('hook', {}).get('technique', 'Unknown')}")
        print(f"    View appeal: {analysis.get('estimated_view_appeal', 'N/A')}/10")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"--- [X] Failed to parse Groq response as JSON: {e} ---")
        # Print first 200 chars of response for debugging
        print(f"    Response preview: {response_text[:200] if 'response_text' in dir() else 'N/A'}...")
        return None
    except Exception as e:
        print(f"--- [X] Groq analysis failed: {e} ---")
        return None


def analyze_youtube_video(video_url: str) -> dict | None:
    """
    Main function: Extracts transcript and analyzes with Groq.
    
    This is the PRIMARY method for learning from rival videos.
    FREE and no rate limits!
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        Analysis dictionary or None if failed.
    """
    # Step 1: Extract transcript
    transcript_data = get_video_transcript(video_url)
    
    if not transcript_data or not transcript_data.get('transcript'):
        print(f"--- [X] No transcript available for {video_url} ---")
        return None
    
    # Step 2: Analyze with Groq
    analysis = analyze_transcript_with_groq(transcript_data)
    
    if analysis:
        # Add source URL to analysis
        analysis['source_url'] = video_url
        analysis['analysis_method'] = 'groq_transcript'
    
    return analysis


if __name__ == '__main__':
    # Test with a sample video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"Testing transcript analyzer with: {test_url}")
    
    result = analyze_youtube_video(test_url)
    if result:
        print("\n--- Full Analysis Result ---")
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed!")
