import re
import random
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base


# --- PROMPT LIBRARY ---

PROMPT_A_LEGACY = """
You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event.

**INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
{prompt_context}
**END INSPIRATION**

**YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

**1. THE CORE IDEA:**
* Pick a relationship dynamic (e.g., sister, boyfriend, boss).
* The conflict MUST have high, almost primal, stakes. It's not just a petty argument; it's about a deep **betrayal**, a threat to **safety**, a shocking **injustice**, or the **protection** of someone innocent.

**2. THE NARRATIVE STRUCTURE (THE FORMULA - FOLLOW THIS EXACTLY):**
* **A. THE HOOK (Start with the 'Explosion'):** Start 'in medias res'. The very first sentence must be the most shocking, confusing, or dramatic moment.
* **B. THE MISDIRECTION (Establish the 'Apparent Villain'):** Create a simple, but *wrong*, conclusion. Make the audience judge the wrong person.
* **C. THE REVEAL (The 'Receipts' and the Twist):** Reveal new, undeniable proof (a text, a photo) that completely flips the story.

**3. WRITING STYLE (CRITICAL):**
* **Show, Don't Tell:** Describe specific actions and their impact, not just emotions.
* **Authentic Voice:** Use a natural, conversational, first-person ("I") tone. The story should be easy to follow.
* **Length:** 200-300 words. Be very strict about this.
* **ABSOLUTELY NO:** No production notes like "[SFX]". No summaries. No morals.

**4. THE OUTPUT FORMAT (Strictly follow this):**
* Start the script with `**Script:**`.
* After the script, on a new line, write a short viral, clickbait-style title starting with `Title: `.

Deliver an unforgettable story with a powerful emotional core and a shocking twist.
"""

PROMPT_B_REDDIT_AITA = """
You are a master storyteller for a viral YouTube channel specializing in the juiciest Reddit stories. Your task is to write a fresh, highly entertaining story that feels like a classic AITA or ProRevenge post.

**INSPIRATION MENU**
To get an idea, look at this menu of popular themes. DO NOT simply copy them. Your goal is to come up with a NEW story that captures a similar vibe. Notice the variety—stories can be about family, partners, friends, roommates, or coworkers. **You must avoid getting stuck on one theme.**
---
{prompt_context}
---
**END MENU**

**YOUR MISSION: WRITE A BANGER STORY**

1.  **THE IDEA:** Pick a relationship dynamic (e.g., sister, boyfriend, boss, roommate) and create a compelling conflict.
2.  **THE SCRIPT:** Write the story from a first-person ("I") perspective.
    * **The Villain:** Create an antagonist who is truly entitled, delusional, or just plain awful.
    * **The Conflict:** Clearly describe the outrageous thing they did to you.
    * **The Payoff:** The ending MUST be a clever, satisfying, "mic-drop" moment of revenge or vindication. This is the most important part.
    * **Tone (CRITICAL):** Write in a natural, conversational style, as if you're venting to your best friend. Use contractions (like "I'm," "don't"), rhetorical questions ("Can you believe it?"), and natural pauses (using ellipses... or em-dashes—) to make the delivery feel authentic and full of emotion.
    * **Length:** 200-300 words.
    * **ABSOLUTELY NO:** Production notes, summaries, or moralizing. Just the juicy story.
3.  **THE OUTPUT FORMAT (Strictly follow this):**
    * Start the script with `**Script:**`.
    * After the script, on a new line, write a viral, clickbait-style title starting with `Title: `.

Deliver an unforgettable story.
"""

PROMPT_C_PETTY_REVENGE = """
You are a writer for a YouTube channel that shares the best petty revenge stories from the internet. Your job is to create a new, original story in that style.

**INSPIRATION MENU (USE FOR VIBE, DON'T COPY):**
---
{prompt_context}
---
**END MENU**

**YOUR MISSION: WRITE A TALE OF PETTY TRIUMPH**

1.  **The Setup:** Describe a situation where someone (a coworker, roommate, stranger) did something incredibly annoying, rude, or obnoxious, but not illegal or fireable. It's the kind of thing you can't officially complain about.
2.  **The Spark:** What was the final straw that made you say, "That's it, I'm getting even"?
3.  **The Plan:** Describe your petty revenge plan. It must be clever, slightly passive-aggressive, and perfectly tailored to the original annoyance. The punishment should fit the crime.
4.  **The Glorious Result:** Tell us how you executed the plan and the satisfying, hilarious outcome. The villain should be annoyed, confused, but unable to prove you did anything wrong.
5.  **Tone:** Conversational, a little bit smug, and very entertaining. Write like you're sharing a hilarious secret with a friend. Use natural language.
6.  **Length:** 200-300 words.
7.  **OUTPUT FORMAT (MANDATORY):**
    * Start with `**Script:**`.
    * Follow with `Title: ` on a new line. The title should be clickbait-y and hint at the petty revenge.

Now, write a story that will make the audience laugh and say, "I wish I'd thought of that."
"""

PROMPT_D_ENTITLED_PEOPLE = """
You are a scriptwriter for a viral YouTube channel that specializes in stories about entitled people getting a reality check. Your task is to write a brand-new, jaw-dropping story.

**INSPIRATION (IDEAS FOR THE FEEL, NOT FOR COPYING):**
---
{prompt_context}
---
**END INSPIRATION**

**YOUR MISSION: WRITE A STORY ABOUT ENTITLEMENT-MEETS-REALITY**

1.  **The Entitled Character:** Introduce us to someone completely out of touch with reality. A "Karen," a "Kevin," a boss who thinks they own you, or a family member who thinks the world revolves around them. Show their entitlement through their absurd demands or actions.
2.  **The Unreasonable Demand:** What was the ridiculous thing they demanded or did? Make it specific and infuriating.
3.  **The "No" Moment:** Describe the moment you (or someone else) refused to comply. This is the turning point.
4.  **The Meltdown & The Consequence:** Detail the tantrum, the disbelief, and the ultimate consequence for the entitled person. They must face the reality that they are not, in fact, the center of the universe. The ending should be satisfying and just.
5.  **Tone:** Write in a first-person, "you won't believe what happened to me" style. It should be engaging, a little dramatic, and ultimately triumphant.
6.  **Length:** 200-300 words.
7.  **OUTPUT FORMAT (FOLLOW EXACTLY):**
    * Start with `**Script:**`.
    * On a new line after the script, provide a viral title starting with `Title: `.

Craft a story that makes people cheer for the person who finally stood up to the entitled character.
"""


# --- HELPER FUNCTION FOR TEXT CLEANING (Used by all strategies) ---
def _clean_and_parse_response(response_text: str) -> dict:
    """Parses the raw LLM response to extract and clean the script and title."""
    title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
    script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

    raw_title = title_match.group(1).strip() if title_match else ""
    # If script isn't found, assume the whole response is the script
    raw_script = script_match.group(1).strip() if script_match else response_text

    def clean_text(text_to_clean):
        # Remove the other part (Title from script, Script from title)
        cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
        # Remove markdown characters
        cleaned = re.sub(r'[`*_~]', '', cleaned)
        return cleaned.strip()

    title = clean_text(raw_title)
    script = clean_text(raw_script)

    # Fallback logic for invalid titles
    if not title or not re.search('[a-zA-Z]', title):
        print("Warning: Parsed title was invalid. Generating a fallback from the script.")
        if script and re.search('[a-zA-Z]', script):
            fallback_title = script.split('.')[0]
            title = (fallback_title[:100] + '...') if len(fallback_title) > 100 else fallback_title
        else:
            title = "AI Generated Story"
            # Ensure script is not empty if title generation failed completely
            if not script or not re.search('[a-zA-Z]', script):
                script = "Could not generate a valid script from the AI response."
    
    return {"script": script, "title": title}

# --- NEW: GENERIC OPENAI PROMPT RUNNER ---
def _run_openai_prompt(prompt_template: str, prompt_context: str, strategy_name: str) -> dict | None:
    """
    Runs a given prompt template with the provided context using the OpenAI model.
    """
    print(f"--- Running OpenAI Strategy: {strategy_name} ---")
    final_prompt = prompt_template.format(prompt_context=prompt_context)
    
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": final_prompt}],
            model="openai/gpt-oss-120b",
            temperature=1.0,
            top_p=1,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in OpenAI Strategy {strategy_name}: {e}")
        traceback.print_exc()
        return None

# --- MAIN DISPATCHER FUNCTION (To be fully implemented in next steps) ---
def generate_optimized_script(recent_topics: list[str] = None, version: str = 'a') -> dict | None:
    """
    Selects a strategy version, generates a script, and returns the result.
    This is the single entry point called by main.py.
    """
    print("--- 🤔 Reddit Story Strategy Agent: Generating optimized script... ---")

    # 1. Gather all data sources
    print("--- 🧠 Knowledge Base: Retrieving all insights ---")
    our_insights = knowledge_base.get_all_insights()
    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        print(f"--- Scanning rival channel feed: {channel_url} ---")
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=3)
        if channel_intel:
            rival_intel.extend(channel_intel)
    
    if rival_intel:
        rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the base prompt context
    prompt_context = "PAST VIDEO PERFORMANCE:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nPOPULAR THEMES FROM OTHER CHANNELS:\n"
    if rival_intel:
        for video in rival_intel[:4]: # Get top 4 videos
            prompt_context += f"- {video['title']} ({video['views']} views)\n"
    else:
        prompt_context += "No rival data available.\n"
        
    prompt_context += "\n\nOUR CORE STORY IDEAS:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL)

    if recent_topics:
        prompt_context += "\n\nRECENTLY COVERED TOPICS (AVOID THESE THEMES):\n"
        prompt_context += "\n".join(f"- {topic}" for topic in recent_topics)

    # 3. Select and run the chosen strategy version
    strategy_map = {
        'a': {"name": "Legacy Vibe", "prompt": PROMPT_A_LEGACY},
        'b': {"name": "AITA/ProRevenge", "prompt": PROMPT_B_REDDIT_AITA},
        'c': {"name": "Petty Revenge", "prompt": PROMPT_C_PETTY_REVENGE},
        'd': {"name": "Entitled People", "prompt": PROMPT_D_ENTITLED_PEOPLE},
    }

    # The version is passed from main.py, which currently selects 'a'-'f'.
    # We'll map all available versions to our four prompts.
    version_to_use = version
    if version not in strategy_map:
        # Map 'e' to 'c' and 'f' to 'd' as a simple way to use all six random slots
        if version == 'e':
            version_to_use = 'c'
        elif version == 'f':
            version_to_use = 'd'
        else:
            print(f"Warning: version '{version}' not found. Defaulting to a random choice.")
            version_to_use = random.choice(list(strategy_map.keys()))

    selected_strategy = strategy_map[version_to_use]
    strategy_name = selected_strategy["name"]
    prompt_template = selected_strategy["prompt"]

    print(f"--- Selected Strategy: '{version_to_use.upper()}' ({strategy_name}) ---")

    result = _run_openai_prompt(
        prompt_template=prompt_template,
        prompt_context=prompt_context,
        strategy_name=strategy_name
    )
    
    if result:
        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {result['title']}")
        return result
    else:
        print(f"--- Strategy '{strategy_name}' failed to generate content. ---")
        return None
