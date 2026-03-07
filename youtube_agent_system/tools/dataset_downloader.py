# youtube_agent_system/tools/dataset_downloader.py
"""
Dataset Downloader — Fetches massive Reddit story datasets from Hugging Face.

Downloads 100K+ real Reddit stories (AITA, ProRevenge, pettyrevenge, etc.),
filters them for quality, scores their viral potential, and returns the top
stories for loading into the training knowledge base.

No web scraping. No API credentials. Just pure dataset downloads.
"""

import os
import json
import re
import hashlib
from typing import Optional

# Category mapping for subreddits
SUBREDDIT_CATEGORIES = {
    "amitheasshole": "AITA",
    "aitah": "AITA",
    "aita": "AITA",
    "prorevenge": "REVENGE",
    "pettyrevenge": "REVENGE",
    "nuclearrevenge": "REVENGE",
    "maliciouscompliance": "REVENGE",
    "relationship_advice": "RELATIONSHIP",
    "relationships": "RELATIONSHIP",
    "tifu": "STORIES",
    "entitledparents": "FAMILY_DRAMA",
    "justnomil": "FAMILY_DRAMA",
    "choosingbeggars": "ENTITLED",
    "confession": "CONFESSION",
    "trueoffmychest": "CONFESSION",
    "bestofredditorupdates": "STORIES",
    "offmychest": "CONFESSION",
    "idontworkherelady": "ENTITLED",
    "talesfromretail": "STORIES",
    "talesfromtechsupport": "STORIES",
}


def _detect_category(text: str, title: str = "") -> str:
    """
    Detects the content category from the story text and title.
    Works even when we don't know the source subreddit.
    """
    combined = (title + " " + text).lower()
    
    # AITA patterns
    aita_patterns = [
        r'\baita\b', r'am i the asshole', r'am i the a-hole',
        r'\bwibta\b', r'would i be the asshole',
        r'aita for', r'aitah',
    ]
    for pattern in aita_patterns:
        if re.search(pattern, combined):
            return "AITA"
    
    # Revenge patterns
    revenge_patterns = [
        r'\brevenge\b', r'got (my|her|his|their) revenge',
        r'malicious compliance', r'pro.?revenge',
        r'petty.?revenge', r'nuclear.?revenge',
        r'sweet.*revenge', r'payback',
    ]
    for pattern in revenge_patterns:
        if re.search(pattern, combined):
            return "REVENGE"
    
    # Family drama patterns
    family_patterns = [
        r'\bmother.?in.?law\b', r'\bfather.?in.?law\b',
        r'\bstep.?mom\b', r'\bstep.?dad\b',
        r'family drama', r'entitled parent',
        r'narcissistic (mom|dad|parent|mother|father)',
        r'\bin-laws?\b',
    ]
    for pattern in family_patterns:
        if re.search(pattern, combined):
            return "FAMILY_DRAMA"
    
    # Relationship patterns  
    relationship_patterns = [
        r'\b(boy|girl)friend\b', r'\bex[\s-]?(bf|gf|husband|wife)\b',
        r'\bcheating\b', r'\bdivorce\b', r'\bbreakup\b',
        r'relationship advice', r'\bengaged\b',
    ]
    for pattern in relationship_patterns:
        if re.search(pattern, combined):
            return "RELATIONSHIP"
    
    # Entitled patterns
    entitled_patterns = [
        r'\bentitled\b', r'choosing beggar',
        r'i don.t work here', r'karen',
    ]
    for pattern in entitled_patterns:
        if re.search(pattern, combined):
            return "ENTITLED"
    
    # Confession patterns
    confession_patterns = [
        r'\bconfession\b', r'\bconfess\b',
        r'off my chest', r'secret.*i.ve.*never',
        r'never told anyone',
    ]
    for pattern in confession_patterns:
        if re.search(pattern, combined):
            return "CONFESSION"
    
    return "STORIES"


def _calculate_quality_score(story: dict) -> float:
    """
    Calculates a quality score (0-10) for a story based on multiple factors.
    Higher score = better story for video content.
    """
    score = 0.0
    
    text = story.get('body', '') or story.get('content', '') or ''
    title = story.get('title', '')
    word_count = len(text.split())
    
    # --- Word count scoring (sweet spot: 200-400 words) ---
    if 200 <= word_count <= 400:
        score += 3.0  # Perfect length for short video
    elif 150 <= word_count <= 500:
        score += 2.0  # Acceptable
    elif 100 <= word_count <= 600:
        score += 1.0  # Can trim
    else:
        score += 0.0  # Too short or too long
    
    # --- Engagement scoring ---
    upvotes = story.get('score', 0) or story.get('ups', 0) or 0
    if upvotes >= 10000:
        score += 3.0
    elif upvotes >= 5000:
        score += 2.5
    elif upvotes >= 1000:
        score += 2.0
    elif upvotes >= 500:
        score += 1.5
    elif upvotes >= 100:
        score += 1.0
    
    # --- Title quality ---
    if title:
        # Dramatic titles with questions or strong emotions
        if '?' in title:
            score += 0.5
        if any(word in title.lower() for word in ['aita', 'revenge', 'told', 'refused', 'caught', 'exposed', 'discovered', 'secret']):
            score += 0.5
        # Title length (not too short, not too long)
        if 30 <= len(title) <= 150:
            score += 0.5
    
    # --- Content quality indicators ---
    # First-person narrative (essential for our format)
    first_person_count = len(re.findall(r'\b(I|I\'m|I\'ve|my|me|mine)\b', text))
    if first_person_count >= 5:
        score += 1.0
    elif first_person_count >= 2:
        score += 0.5
    
    # Has paragraphs (structured content)
    if text.count('\n') >= 2:
        score += 0.5
    
    # Has dialogue or quotes
    if '"' in text or "'" in text:
        score += 0.5
    
    return min(score, 10.0)


def _clean_story_text(text: str) -> str:
    """Cleans up story text for use as training data."""
    if not text:
        return ""
    
    # Remove Reddit formatting
    text = re.sub(r'\[removed\]', '', text)
    text = re.sub(r'\[deleted\]', '', text)
    text = re.sub(r'Edit:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'Update:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'TL;?DR:?.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'TLDR:?.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def download_aita_dataset(max_stories: int = 5000) -> list[dict]:
    """
    Downloads the AITA Reddit dataset from Hugging Face.
    
    This dataset has 100K+ AITA stories with titles, body text, and scores.
    
    Args:
        max_stories: Maximum number of stories to process (for speed)
        
    Returns:
        List of story dictionaries ready for quality scoring
    """
    print("[DL] Downloading AITA dataset from Hugging Face...")
    print("   (This may take a moment on first run — dataset is cached after)")
    
    try:
        from datasets import load_dataset
    except ImportError:
        print("[X] Error: 'datasets' library not installed. Run: pip install datasets")
        return []
    
    stories = []
    
    # --- Dataset 1: OsamaBsher/AITA-Reddit-Dataset (100K+ stories) ---
    try:
        print("\n[PKG] Loading OsamaBsher/AITA-Reddit-Dataset...")
        dataset = load_dataset("OsamaBsher/AITA-Reddit-Dataset", split="train", trust_remote_code=True)
        print(f"   Found {len(dataset)} entries")
        
        # Get column names to handle different schemas
        columns = dataset.column_names
        print(f"   Columns: {columns}")
        
        count = 0
        for row in dataset:
            if count >= max_stories:
                break
            
            # Try to extract title and body from various column name formats
            title = ""
            body = ""
            score_val = 0
            
            for col in columns:
                col_lower = col.lower()
                value = row.get(col, "")
                if value is None:
                    continue
                    
                if col_lower in ('title', 'post_title'):
                    title = str(value)
                elif col_lower in ('body', 'text', 'selftext', 'post_text', 'content', 'post_body'):
                    body = str(value)
                elif col_lower in ('score', 'ups', 'upvotes', 'num_upvotes'):
                    try:
                        score_val = int(value)
                    except (ValueError, TypeError):
                        score_val = 0
            
            # Skip empty stories
            if not body or len(body.split()) < 80:
                continue
            
            # Clean the text
            body = _clean_story_text(body)
            if not body or body == "[removed]" or body == "[deleted]":
                continue
            
            # Create story dict
            story_id = hashlib.md5(f"{title}_{body[:100]}".encode()).hexdigest()[:12]
            
            stories.append({
                'id': f"hf_aita_{story_id}",
                'title': title,
                'body': body,
                'score': score_val,
                'source': 'huggingface/OsamaBsher/AITA-Reddit-Dataset',
                'subreddit': 'AmItheAsshole',
                'word_count': len(body.split()),
            })
            count += 1
        
        print(f"   [OK] Extracted {len(stories)} valid stories from Dataset 1")
        
    except Exception as e:
        print(f"   [!] Error loading Dataset 1: {e}")
    
    # --- Dataset 2: jeanong2/AITA-datasets (10K-100K stories, different format) ---
    try:
        print("\n[PKG] Loading jeanong2/AITA-datasets...")
        dataset2 = load_dataset("jeanong2/AITA-datasets", split="train", trust_remote_code=True)
        print(f"   Found {len(dataset2)} entries")
        
        columns2 = dataset2.column_names
        print(f"   Columns: {columns2}")
        
        existing_ids = {s['id'] for s in stories}
        count2 = 0
        
        for row in dataset2:
            if count2 >= max_stories // 2:  # Don't overload from one source
                break
            
            title = ""
            body = ""
            score_val = 0
            
            for col in columns2:
                col_lower = col.lower()
                value = row.get(col, "")
                if value is None:
                    continue
                    
                if col_lower in ('title', 'post_title'):
                    title = str(value)
                elif col_lower in ('body', 'text', 'selftext', 'post_text', 'content', 'post_body'):
                    body = str(value)
                elif col_lower in ('score', 'ups', 'upvotes', 'num_upvotes'):
                    try:
                        score_val = int(value)
                    except (ValueError, TypeError):
                        score_val = 0
            
            if not body or len(body.split()) < 80:
                continue
            
            body = _clean_story_text(body)
            if not body or body == "[removed]" or body == "[deleted]":
                continue
            
            story_id = hashlib.md5(f"{title}_{body[:100]}".encode()).hexdigest()[:12]
            full_id = f"hf_aita2_{story_id}"
            
            if full_id in existing_ids:
                continue
            
            stories.append({
                'id': full_id,
                'title': title,
                'body': body,
                'score': score_val,
                'source': 'huggingface/jeanong2/AITA-datasets',
                'subreddit': 'AmItheAsshole',
                'word_count': len(body.split()),
            })
            existing_ids.add(full_id)
            count2 += 1
        
        print(f"   [OK] Extracted {count2} additional stories from Dataset 2")
        
    except Exception as e:
        print(f"   [!] Error loading Dataset 2: {e}")
    
    print(f"\n[STAT] Total raw stories collected: {len(stories)}")
    return stories


def score_and_filter_stories(
    stories: list[dict],
    min_quality_score: float = 3.0,
    min_word_count: int = 100,
    max_word_count: int = 600,
    top_n: int = 3000
) -> list[dict]:
    """
    Scores all stories and returns the top N highest quality ones.
    
    Args:
        stories: Raw story list from download functions
        min_quality_score: Minimum quality score to keep
        min_word_count: Minimum word count
        max_word_count: Maximum word count
        top_n: Number of top stories to return
        
    Returns:
        Sorted list of the best stories with quality scores
    """
    print(f"\n[FILTER] Scoring {len(stories)} stories for quality...")
    
    scored = []
    for story in stories:
        wc = story.get('word_count', 0)
        if wc < min_word_count or wc > max_word_count:
            continue
        
        # Detect category
        story['category'] = _detect_category(
            story.get('body', ''),
            story.get('title', '')
        )
        
        # Score quality
        story['quality_score'] = _calculate_quality_score(story)
        
        if story['quality_score'] >= min_quality_score:
            scored.append(story)
    
    # Sort by quality score (descending)
    scored.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Take top N
    result = scored[:top_n]
    
    # Print category breakdown
    categories = {}
    for s in result:
        cat = s.get('category', 'UNKNOWN')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n[STAT] Quality Filter Results:")
    print(f"   Passed filter: {len(scored)} / {len(stories)}")
    print(f"   Selected top: {len(result)}")
    print(f"\n   Category breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"     {cat}: {count} stories")
    
    return result


def save_training_corpus(stories: list[dict], filepath: str = None) -> str:
    """
    Saves the curated stories to a JSON file for the training corpus.
    
    Args:
        stories: Curated story list
        filepath: Where to save (defaults to generated_assets/training_corpus.json)
        
    Returns:
        Path to the saved file
    """
    if filepath is None:
        from .. import config
        filepath = os.path.join(config.ASSETS_DIR, "training_corpus.json")
    
    corpus = {
        'version': '1.0',
        'total_stories': len(stories),
        'categories': {},
        'stories': stories,
    }
    
    # Count categories
    for s in stories:
        cat = s.get('category', 'UNKNOWN')
        corpus['categories'][cat] = corpus['categories'].get(cat, 0) + 1
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVE] Training corpus saved to: {filepath}")
    print(f"   Total stories: {corpus['total_stories']}")
    print(f"   File size: {os.path.getsize(filepath) / (1024*1024):.1f} MB")
    
    return filepath


def load_training_corpus(filepath: str = None) -> list[dict]:
    """
    Loads a previously saved training corpus.
    
    Returns:
        List of story dictionaries
    """
    if filepath is None:
        from .. import config
        filepath = os.path.join(config.ASSETS_DIR, "training_corpus.json")
    
    if not os.path.exists(filepath):
        print(f"[!] No training corpus found at: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        corpus = json.load(f)
    
    stories = corpus.get('stories', [])
    print(f"[LOAD] Loaded training corpus: {len(stories)} stories")
    return stories


# ============================================================
# ADDITIONAL DATASET DOWNLOADERS
# ============================================================

def _extract_stories_generic(dataset, source_name: str, subreddit: str,
                              max_stories: int, existing_ids: set) -> list[dict]:
    """
    Generic extractor that handles various HuggingFace dataset column schemas.
    Returns extracted story dicts and updates existing_ids in-place.
    """
    columns = dataset.column_names
    stories = []
    count = 0

    for row in dataset:
        if count >= max_stories:
            break

        title = ""
        body = ""
        score_val = 0

        for col in columns:
            cl = col.lower()
            value = row.get(col, "")
            if value is None:
                continue
            if cl in ('title', 'post_title'):
                title = str(value)
            elif cl in ('body', 'text', 'selftext', 'post_text', 'content',
                         'post_body', 'document', 'tldr', 'post'):
                candidate = str(value)
                # Keep the longer field as body
                if len(candidate) > len(body):
                    body = candidate
            elif cl in ('score', 'ups', 'upvotes', 'num_upvotes'):
                try:
                    score_val = int(value)
                except (ValueError, TypeError):
                    pass
            elif cl == 'subreddit':
                subreddit = str(value)

        if not body or len(body.split()) < 80:
            continue

        body = _clean_story_text(body)
        if not body or body in ("[removed]", "[deleted]"):
            continue

        story_id = hashlib.md5(f"{title}_{body[:100]}".encode()).hexdigest()[:12]
        full_id = f"hf_{subreddit[:8]}_{story_id}"

        if full_id in existing_ids:
            continue

        stories.append({
            'id': full_id,
            'title': title,
            'body': body,
            'score': score_val,
            'source': f'huggingface/{source_name}',
            'subreddit': subreddit,
            'word_count': len(body.split()),
        })
        existing_ids.add(full_id)
        count += 1

    return stories


def download_confessions_dataset(max_stories: int = 3000) -> list[dict]:
    """
    Downloads confession stories from SocialGrep/one-million-reddit-confessions.
    Contains posts from r/confession and r/TrueOffMyChest (1M+ posts).
    """
    print("\n[DL] Downloading Confessions dataset...")
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    stories = []
    existing_ids = set()

    try:
        print("   [PKG] Loading SocialGrep/one-million-reddit-confessions...")
        ds = load_dataset(
            "SocialGrep/one-million-reddit-confessions",
            split="train",
            streaming=True,  # Stream to avoid downloading full 1M into RAM
        )
        columns_printed = False
        count = 0

        for row in ds:
            if count >= max_stories:
                break

            if not columns_printed:
                print(f"   Columns: {list(row.keys())}")
                columns_printed = True

            title = str(row.get('title', '') or '')
            body = str(row.get('selftext', '') or row.get('body', '') or
                       row.get('text', '') or '')

            if not body or len(body.split()) < 80:
                continue

            body = _clean_story_text(body)
            if not body or body in ("[removed]", "[deleted]"):
                continue

            score_val = 0
            try:
                score_val = int(row.get('score', 0) or 0)
            except (ValueError, TypeError):
                pass

            sub = str(row.get('subreddit', 'confession') or 'confession')
            story_id = hashlib.md5(f"{title}_{body[:100]}".encode()).hexdigest()[:12]
            full_id = f"hf_conf_{story_id}"

            if full_id in existing_ids:
                continue

            stories.append({
                'id': full_id,
                'title': title,
                'body': body,
                'score': score_val,
                'source': 'huggingface/SocialGrep/one-million-reddit-confessions',
                'subreddit': sub,
                'word_count': len(body.split()),
                'category': 'CONFESSION',
            })
            existing_ids.add(full_id)
            count += 1

            if count % 500 == 0:
                print(f"   ... processed {count} confession stories")

        print(f"   [OK] Extracted {len(stories)} confession stories")

    except Exception as e:
        print(f"   [!] Error loading confessions dataset: {e}")

    return stories


def download_tifu_dataset(max_stories: int = 2000) -> list[dict]:
    """
    Downloads TIFU (Today I F***ed Up) stories from ctr4si/reddit_tifu.
    """
    print("\n[DL] Downloading TIFU dataset...")
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    stories = []
    existing_ids = set()

    # --- Primary: ctr4si/reddit_tifu (long stories) ---
    try:
        print("   [PKG] Loading ctr4si/reddit_tifu (long)...")
        ds = load_dataset("ctr4si/reddit_tifu", "long", split="train",
                          trust_remote_code=True)
        print(f"   Found {len(ds)} entries")
        print(f"   Columns: {ds.column_names}")

        extracted = _extract_stories_generic(
            ds, "ctr4si/reddit_tifu", "tifu", max_stories, existing_ids
        )
        # Override category
        for s in extracted:
            s['category'] = 'STORIES'
        stories.extend(extracted)
        print(f"   [OK] Extracted {len(extracted)} TIFU stories")

    except Exception as e:
        print(f"   [!] Error loading TIFU dataset: {e}")

    # --- Fallback: Oguzz07/reddit-tifu-dataset ---
    remaining = max_stories - len(stories)
    if remaining > 0:
        try:
            print("   [PKG] Loading Oguzz07/reddit-tifu-dataset...")
            ds2 = load_dataset("Oguzz07/reddit-tifu-dataset", split="train",
                               trust_remote_code=True)
            print(f"   Found {len(ds2)} entries")

            extracted2 = _extract_stories_generic(
                ds2, "Oguzz07/reddit-tifu-dataset", "tifu", remaining, existing_ids
            )
            for s in extracted2:
                s['category'] = 'STORIES'
            stories.extend(extracted2)
            print(f"   [OK] Extracted {len(extracted2)} additional TIFU stories")

        except Exception as e:
            print(f"   [!] Error loading fallback TIFU dataset: {e}")

    print(f"   Total TIFU stories: {len(stories)}")
    return stories


def download_relationship_dataset(max_stories: int = 2000) -> list[dict]:
    """
    Downloads relationship advice stories from trl-lib/tldr.
    Filters for relationship-related subreddits.
    """
    print("\n[DL] Downloading Relationship stories...")
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    stories = []
    existing_ids = set()

    relationship_subs = {
        'relationships', 'relationship_advice', 'dating_advice',
        'breakups', 'marriage', 'divorce',
    }

    try:
        print("   [PKG] Loading trl-lib/tldr...")
        ds = load_dataset("trl-lib/tldr", split="train",
                          trust_remote_code=True)
        print(f"   Found {len(ds)} entries")
        print(f"   Columns: {ds.column_names}")

        count = 0
        for row in ds:
            if count >= max_stories:
                break

            sub = str(row.get('subreddit', '') or '').lower().strip()
            # Accept relationship subs, or posts that sound like relationship content
            body = str(row.get('post', '') or row.get('content', '') or
                       row.get('text', '') or row.get('document', '') or '')
            title = str(row.get('title', '') or '')

            is_relationship_sub = sub in relationship_subs
            is_relationship_content = _detect_category(body, title) == "RELATIONSHIP"

            if not is_relationship_sub and not is_relationship_content:
                continue

            if not body or len(body.split()) < 80:
                continue

            body = _clean_story_text(body)
            if not body or body in ("[removed]", "[deleted]"):
                continue

            score_val = 0
            try:
                score_val = int(row.get('score', 0) or 0)
            except (ValueError, TypeError):
                pass

            story_id = hashlib.md5(f"{title}_{body[:100]}".encode()).hexdigest()[:12]
            full_id = f"hf_rel_{story_id}"

            if full_id in existing_ids:
                continue

            stories.append({
                'id': full_id,
                'title': title,
                'body': body,
                'score': score_val,
                'source': 'huggingface/trl-lib/tldr',
                'subreddit': sub or 'relationship_advice',
                'word_count': len(body.split()),
                'category': 'RELATIONSHIP',
            })
            existing_ids.add(full_id)
            count += 1

        print(f"   [OK] Extracted {len(stories)} relationship stories")

    except Exception as e:
        print(f"   [!] Error loading relationship dataset: {e}")

    return stories


# ============================================================
# SYNTHETIC STORY GENERATION (for categories without datasets)
# ============================================================

# Seed titles for generating synthetic revenge stories
REVENGE_SEED_TITLES = [
    "My neighbor kept stealing my packages so I set up a glitter bomb that ruined his car",
    "My boss took credit for my project so I made sure the CEO knew the truth",
    "My roommate ate my food for months so I replaced everything with sugar-free versions",
    "My landlord refused to fix our heating so I withheld rent legally and he got fined",
    "My coworker kept sabotaging my work so I documented everything and got them fired",
    "The HOA president fined me for my garden gnomes so I maliciously complied",
    "My ex keyed my car so I sent the dashcam footage to their boss",
    "My sister stole my wedding fund so I exposed her lies at Christmas dinner",
    "The school bully picked on my kid so I taught them the perfect legal comeback",
    "My aunt tried to steal my inheritance so I hired a lawyer and she lost everything",
    "My professor accused me of cheating so I proved they were wrong in front of the dean",
    "My brother-in-law scammed my parents out of $50K so I gathered evidence and pressed charges",
    "My old manager gave me a bad reference so I reported their illegal practices",
    "The car dealer tried to rip me off so I recorded the whole conversation",
    "My friend group abandoned me at a party so I walked away and never looked back",
    "A Karen tried to get me fired for following rules so I maliciously complied until she left",
    "My upstairs neighbor blasted music at 3am so I found a creative legal solution",
    "My college roommate spread rumors about me so I exposed their academic fraud",
    "A contractor tried to overcharge my elderly parents so I showed up with a building inspector",
    "My former best friend stole my business idea so I outperformed them in every way",
    "I caught my mechanic charging me for work he never did so I set a trap",
    "My HOA tried to force me to remove my solar panels so I found an obscure bylaw that protected me",
    "A wedding vendor ghosted us after taking our deposit so I destroyed their Yelp page with evidence",
    "My neighbor cut down my tree that was on MY property so I sued and won big",
    "My manager denied my vacation then took one himself so I CC'd HR on everything",
    "The school principal punished my kid unfairly so I brought a lawyer to the next meeting",
    "My in-laws tried to crash my wedding so I hired security and they were escorted out",
    "A scammer targeted my grandma so I wasted 3 months of their time pretending to be a victim",
    "My coworker stole my lunch every day so I made a special batch just for them",
    "The customer who screamed at me got exactly what they asked for and regretted it",
]

FAMILY_DRAMA_SEED_TITLES = [
    "My mother-in-law wore white to my wedding and I had red wine ready",
    "My stepmom tried to replace my dead mother's photos and I put them all back",
    "My entitled parents expected me to fund their retirement after they kicked me out at 18",
    "My sister demanded I give her my inheritance because she has kids and I don't",
    "My narcissistic mother showed up uninvited to my baby shower and caused a scene",
    "My father-in-law told my kids I'm not their real parent and I lost it",
    "I cut off my toxic family after 25 years and they showed up at my workplace",
    "My brother expected me to raise his kids while he partied every weekend",
    "My mother-in-law rearranged my entire house while I was at work",
    "My parents played favorites my whole life and were shocked when I stopped calling",
    "My entitled aunt demanded I give her daughter my prom dress because hers was ugly",
    "My stepdad tried to give away my dead father's belongings without asking me",
    "My sister told everyone I was infertile at a family dinner to get attention",
    "My mother moved in without asking and started redecorating my house",
    "My in-laws expected us to host every holiday and got angry when we said no",
    "My father told me he wished I was never born and now wants me to take care of him",
    "My cousin announced her pregnancy at MY wedding reception",
    "My mother-in-law secretly fed my allergic child the food I said was dangerous",
    "My parents gave my college fund to my golden child sibling and expected me to be okay",
    "My entitled grandmother tried to take over my parenting and I had to set firm boundaries",
    "My sister-in-law expected me to be a free babysitter because I work from home",
    "My father secretly changed his will and left everything to his new wife",
    "My mother publicly shamed me for not breastfeeding at a family gathering",
    "My in-laws tried to name my baby without my consent and were furious when I refused",
    "My brother stole money from our dying father and blamed it on me",
    "My stepmother threw away all my childhood belongings when I left for college",
    "My parents showed up to my child-free wedding with my teenage siblings",
    "My entitled mother demanded a key to my new house and threw a tantrum when I said no",
    "My sister went behind my back and told my employer about my mental health struggles",
    "My father-in-law gifted my husband a car but said I couldn't drive it because I'm a woman",
]


def generate_synthetic_stories(
    category: str,
    seed_titles: list[str],
    count: int = 200,
    batch_size: int = 5,
) -> list[dict]:
    """
    Generates synthetic training stories using Groq API for categories
    where no HuggingFace dataset exists.

    Args:
        category: REVENGE or FAMILY_DRAMA
        seed_titles: List of seed titles to generate stories from
        count: Total stories to generate
        batch_size: Stories per API call

    Returns:
        List of synthetic story dicts
    """
    print(f"\n[GEN] Generating {count} synthetic {category} stories via LLM...")

    try:
        from .. import config
        from groq import Groq
    except ImportError:
        print("   [!] Groq not available for synthetic generation")
        return []

    if not config.GROQ_API_KEY:
        print("   [!] GROQ_API_KEY not configured")
        return []

    client = Groq(api_key=config.GROQ_API_KEY)
    stories = []
    generated = 0

    # Cycle through seed titles, generating multiple per title
    for i in range(0, count, batch_size):
        if generated >= count:
            break

        # Pick seed titles for this batch
        batch_titles = []
        for j in range(batch_size):
            idx = (i + j) % len(seed_titles)
            batch_titles.append(seed_titles[idx])

        titles_list = "\n".join(f"{n+1}. {t}" for n, t in enumerate(batch_titles))

        prompt = f"""You are an expert Reddit storyteller. Generate {batch_size} unique, compelling first-person Reddit stories based on these titles. Each story should be 200-350 words.

TITLES:
{titles_list}

RULES:
- Write in first person ("I") perspective
- Conversational, authentic Reddit tone
- Include specific details (names, amounts, places, times)
- Strong emotional hook in the first sentence
- Clear conflict, building tension, satisfying resolution
- No moral lectures — let events speak for themselves
- Each story should feel DIFFERENT and UNIQUE
- Use contractions and natural speech patterns

OUTPUT FORMAT — write each story EXACTLY like this:
===STORY===
TITLE: [title]
BODY: [full story text]
===END===

Generate all {batch_size} stories now:"""

        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.9,
                max_tokens=4096,
            )

            raw = response.choices[0].message.content or ""

            # Parse stories from response
            story_blocks = raw.split("===STORY===")
            for block in story_blocks:
                if "===END===" not in block:
                    continue

                block = block.split("===END===")[0].strip()
                title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', block)
                body_match = re.search(r'BODY:\s*(.+)', block, re.DOTALL)

                if not title_match or not body_match:
                    continue

                title = title_match.group(1).strip()
                body = body_match.group(1).strip()

                if len(body.split()) < 100:
                    continue

                story_id = hashlib.md5(
                    f"syn_{title}_{body[:50]}".encode()
                ).hexdigest()[:12]

                stories.append({
                    'id': f"syn_{category.lower()[:4]}_{story_id}",
                    'title': title,
                    'body': body,
                    'score': 5000,  # Give decent score since these are curated
                    'source': 'synthetic/groq-llama3.3',
                    'subreddit': 'synthetic',
                    'word_count': len(body.split()),
                    'category': category,
                    'quality_score': 5.0,  # Pre-scored
                })
                generated += 1

            if generated % 20 == 0 or generated >= count:
                print(f"   ... generated {generated}/{count} {category} stories")

        except Exception as e:
            print(f"   [!] API error on batch {i}: {e}")
            import time
            time.sleep(2)  # Rate limit cooldown
            continue

    print(f"   [OK] Generated {len(stories)} synthetic {category} stories")
    return stories


# === MAIN PIPELINE FUNCTION ===

def run_full_download_pipeline(
    max_download: int = 5000,
    top_n: int = 5000,
    min_quality: float = 3.0,
    save: bool = True
) -> list[dict]:
    """
    Runs the full download -> filter -> save pipeline for ALL categories.

    Downloads from:
    - AITA datasets (HuggingFace)
    - Confessions dataset (HuggingFace, 1M posts)
    - TIFU dataset (HuggingFace)
    - Relationship advice (HuggingFace)
    - Synthetic revenge stories (Groq LLM)
    - Synthetic family drama stories (Groq LLM)

    Args:
        max_download: Max stories to download per source
        top_n: Top N stories to keep after scoring
        min_quality: Minimum quality score
        save: Whether to save to disk

    Returns:
        List of curated, high-quality stories across all categories
    """
    print("=" * 60)
    print("[GO] FULL MULTI-CATEGORY STORY DOWNLOAD PIPELINE")
    print("=" * 60)

    all_stories = []

    # --- 1. AITA (existing) ---
    aita = download_aita_dataset(max_stories=max_download)
    all_stories.extend(aita)

    # --- 2. Confessions ---
    confessions = download_confessions_dataset(max_stories=min(max_download, 3000))
    all_stories.extend(confessions)

    # --- 3. TIFU ---
    tifu = download_tifu_dataset(max_stories=min(max_download, 2000))
    all_stories.extend(tifu)

    # --- 4. Relationship ---
    relationship = download_relationship_dataset(max_stories=min(max_download, 2000))
    all_stories.extend(relationship)

    # --- 5. Synthetic Revenge ---
    revenge = generate_synthetic_stories(
        category="REVENGE",
        seed_titles=REVENGE_SEED_TITLES,
        count=200,
        batch_size=5,
    )
    all_stories.extend(revenge)

    # --- 6. Synthetic Family Drama ---
    family = generate_synthetic_stories(
        category="FAMILY_DRAMA",
        seed_titles=FAMILY_DRAMA_SEED_TITLES,
        count=200,
        batch_size=5,
    )
    all_stories.extend(family)

    print(f"\n[STAT] Total raw stories from ALL sources: {len(all_stories)}")

    if not all_stories:
        print("[X] No stories downloaded. Check your internet connection.")
        return []

    # Score & Filter
    curated = score_and_filter_stories(
        all_stories,
        min_quality_score=min_quality,
        top_n=top_n
    )

    # Save
    if save and curated:
        save_training_corpus(curated)

    print("\n" + "=" * 60)
    print(f"[OK] PIPELINE COMPLETE -- {len(curated)} high-quality stories ready")
    print("=" * 60)

    return curated


if __name__ == '__main__':
    # Run the full pipeline
    stories = run_full_download_pipeline(
        max_download=5000,
        top_n=3000,
        min_quality=3.0
    )
    
    if stories:
        # Show some examples
        print("\n\n[BOOK] Sample stories:")
        for s in stories[:3]:
            print(f"\n  [{s['quality_score']:.1f}] [{s['category']}] {s['title'][:80]}...")
            print(f"  Words: {s['word_count']} | Score: {s['score']}")
            print(f"  Preview: {s['body'][:150]}...")
