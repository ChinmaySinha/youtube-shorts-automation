import re
import random
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base


# --- EXPANDED & REFINED PROMPT LIBRARY ---

PROMPT_A_BROKEN_STORY = """
You are a master storyteller, an expert in crafting unforgettable viral narratives in the style of the "Broken Stories" genre. Your only job is to write a captivating, first-person story that feels raw and real, like a confession.

**INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
{prompt_context}
**END INSPIRATION**

**YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

**1. THE CORE IDEA:**
* Pick a close relationship (family, partner, best friend).
* The conflict MUST be about a deep, primal betrayal, a shocking injustice, or the discovery of a devastating secret. The stakes are intensely personal and emotional.

**2. THE NARRATIVE STRUCTURE (FOLLOW THIS EXACTLY):**
* **A. THE HOOK (The "In Medias Res" Explosion):** Your very first sentence must be the most dramatic moment of the story. No setup. Start with the immediate aftermath of a shocking event. Example: "The paternity test results weren't just negative; they said I was related to my wife's sister."
* **B. THE MISDIRECTION (The Apparent Villain):** Build the story to make the audience suspect the wrong person or the wrong motive. Create a simple but incorrect conclusion.
* **C. THE REVEAL (The "Receipts"):** Introduce undeniable proof (a hidden letter, a DNA result, a revealing photo, a recorded confession) that shatters the misdirection and exposes the shocking, true nature of the betrayal.

**3. WRITING STYLE (CRITICAL):**
* **Voice:** Raw, emotional, first-person ("I"). Write as if you're still processing the shock.
* **Pacing:** Short, impactful sentences. Easy to follow.
* **Length:** Strictly 200-300 words.
* **ABSOLUTELY NO:** Summaries, morals, or production notes.

**4. THE OUTPUT FORMAT (MANDATORY):**
* Start with `**Script:**`.
* After the script, on a new line, write a viral, clickbait-style title starting with `Title: `.
"""

PROMPT_B_AITA_JUDGEMENT = """
You are a top-tier Reddit storyteller for a viral YouTube channel. Your job is to write a fresh, highly engaging story that feels like a classic "Am I The A-hole?" post where the answer is CLEARLY "Not the A-hole."

**INSPIRATION MENU (USE FOR VIBE, DON'T COPY):**
{prompt_context}
**END MENU**

**YOUR MISSION: WRITE A STORY OF EPIC VINDICATION**

1.  **The Villain:** Create a truly entitled, delusional, or manipulative antagonist (family member, partner, coworker, etc.).
2.  **The Unreasonable Situation:** Describe the absolutely outrageous thing they demanded or did to you. The audience's jaw should drop.
3.  **The Boundary:** Detail the clear, reasonable boundary you set.
4.  **The "Mic-Drop" Payoff:** The ending must be a clever, satisfying moment where you enforce your boundary and the villain gets exactly what they deserve. This is the most important part. The audience should feel a rush of secondhand victory.
5.  **Tone (CRITICAL):** Write in a natural, conversational, "venting to a friend" style. Use contractions (I'm, they're), rhetorical questions ("Right?!"), and ellipses... to create an authentic, emotional delivery.
6.  **Length:** Strictly 200-300 words.
7.  **ABSOLUTELY NO:** Production notes or summaries. Just the juicy story.

**THE OUTPUT FORMAT (MANDATORY):**
* Start with `**Script:**`.
* After the script, on a new line, write a viral AITA-style title starting with `Title: `.
"""

PROMPT_C_PETTY_REVENGE = """
You are a writer for a YouTube channel that shares the best petty revenge stories. Your job is to create a new, original story that is both hilarious and deeply satisfying.

**INSPIRATION MENU (USE FOR VIBE, DON'T COPY):**
{prompt_context}
**END MENU**

**YOUR MISSION: WRITE A TALE OF PETTY TRIUMPH**

1.  **The Annoyance:** Describe a recurring, infuriatingly obnoxious thing someone does (e.g., a coworker stealing your specific creamer, a roommate leaving passive-aggressive notes). It must be something you can't officially complain about.
2.  **The Final Straw:** What was the one incident that pushed you over the edge?
3.  **The Petty Plan:** Describe your brilliantly simple, passive-aggressive revenge. The punishment must perfectly fit the crime. It should be subtle, causing maximum confusion and annoyance to the target.
4.  **The Glorious Result:** Detail the outcome. The target must be annoyed but unable to prove you did anything, leaving you to watch the quiet chaos you've created.
5.  **Tone:** Conversational, a little bit smug, and highly entertaining. Write like you're sharing a genius secret.
6.  **Length:** Strictly 200-300 words.

**OUTPUT FORMAT (MANDATORY):**
* Start with `**Script:**`.
* Follow with `Title: ` on a new line. The title should be clickbait-y and hint at the petty revenge.
"""

PROMPT_D_KAREN_CHECKMATE = """
You are a scriptwriter for a viral YouTube channel specializing in stories about entitled people getting a reality check. Your task is to write a brand-new, jaw-dropping story.

**INSPIRATION (IDEAS FOR THE FEEL, NOT FOR COPYING):**
{prompt_context}
**END INSPIRATION**

**YOUR MISSION: WRITE AN ENTITLEMENT-MEETS-REALITY STORY**

1.  **The Entitled "Karen":** Introduce someone completely out of touch. Show their entitlement through an absurd demand, a condescending attitude, or a belief that rules don't apply to them.
2.  **The Unreasonable Demand:** What was the ridiculous thing they demanded? Make it specific and infuriating.
3.  **The "Malicious Compliance" or "The Firm No":** Describe the moment you (or someone else) refused to comply, often by following the rules *to the letter* in a way that thwarts them, or by simply giving a firm, unshakeable "no."
4.  **The Meltdown & The Consequence:** Detail the tantrum, the disbelief, and the ultimate, satisfying consequence for the entitled person. They must face the reality that they are not the center of the universe.
5.  **Tone:** A first-person, "you won't believe this" style. Engaging, dramatic, and ultimately triumphant.
6.  **Length:** Strictly 200-300 words.

**OUTPUT FORMAT (FOLLOW EXACTLY):**
* Start with `**Script:**`.
* On a new line, provide a viral title starting with `Title: `.
"""

PROMPT_E_UNEXPECTED_KINDNESS = """
You are a storyteller for a viral channel, but your goal today is different. You need to write a story that restores people's faith in humanity, inspired by heartwarming "Reddit Biker" style human-interest tales.

**INSPIRATION (USE FOR VIBE, DON'T COPY):**
{prompt_context}
**END INSPIRATION**

**YOUR MISSION: CRAFT A STORY OF UNEXPECTED KINDNESS**

1.  **The Setup (The Bad Day):** Start by describing a genuinely bad, frustrating, or lonely day from a first-person perspective. The narrator should be cynical, tired, or at their wit's end. Set a scene of mundane misery (e.g., car trouble in the rain, a tough day at work, feeling invisible in a crowd).
2.  **The Turn (The Small Act):** Introduce an unexpected moment of pure, selfless kindness from a stranger. It shouldn't be a grand, life-saving gesture. It should be small, specific, and unprompted. (e.g., an elderly person sharing their umbrella, someone paying for their coffee, a quiet, knowing look of support).
3.  **The Impact (The Shift in Perspective):** Describe the narrator's reaction. It should be one of surprise, maybe even confusion, that melts into genuine gratitude. The small act doesn't fix their whole day, but it fundamentally changes their emotional state and reminds them of the good in the world.
4.  **Tone:** Starts cynical and weary, transitions to surprised and warm. Must feel authentic and grounded, not overly sentimental or cheesy.
5.  **Length:** Strictly 200-300 words.

**OUTPUT FORMAT (MANDATORY):**
* Start with `**Script:**`.
* On a new line, provide a wholesome, viral title starting with `Title: `.
"""

PROMPT_F_ESCAPING_THE_GASLIGHTER = """
You are a writer for a channel that tells deep, psychologically resonant stories, in the vein of the most compelling "Broken Stories" episodes. Your mission is to write a story about the moment someone realized they were being gaslit.

**INSPIRATION (USE FOR VIBE, DON'T COPY):**
{prompt_context}
**END INSPIRATION**

**YOUR MISSION: WRITE A STORY OF SHATTERING AN ILLUSION**

1.  **The Setup (The Confusion):** From a first-person ("I") perspective, describe a situation where you constantly feel like you're going crazy. Show the gaslighter in action—twisting your words, denying things they said, making you doubt your memory. Don't say "he was gaslighting me." Show it. Example: "He swore he never said he'd pick up our son, and for the tenth time that month, I started to believe my brain was broken."
2.  **The "Glitch" (The Undeniable Proof):** Describe the moment the gaslighter made a mistake. You find undeniable proof that your memory was right all along. A saved text message they thought was deleted, a voicemail, an email, or a third-person witness who confirms your version of events.
3.  **The "Snap" (The Moment of Clarity):** This is the climax. Describe the feeling of the fog instantly lifting. It's not anger, but a chilling, terrifying clarity. You realize it was never you; it was manipulation.
4.  **The Aftermath (The First Step):** The story ends not with a huge confrontation, but with a quiet, powerful first step towards freedom. Deleting their number, packing a bag, making a phone call. It's an ending of silent empowerment.
5.  **Length:** Strictly 200-300 words.

**OUTPUT FORMAT (MANDATORY):**
* Start with `**Script:**`.
* On a new line, provide a powerful, intriguing title starting with `Title: `.
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
        'a': {"name": "Broken Story", "prompt": PROMPT_A_BROKEN_STORY},
        'b': {"name": "AITA Judgement", "prompt": PROMPT_B_AITA_JUDGEMENT},
        'c': {"name": "Petty Revenge", "prompt": PROMPT_C_PETTY_REVENGE},
        'd': {"name": "Karen Checkmate", "prompt": PROMPT_D_KAREN_CHECKMATE},
        'e': {"name": "Unexpected Kindness", "prompt": PROMPT_E_UNEXPECTED_KINDNESS},
        'f': {"name": "Escaping the Gaslighter", "prompt": PROMPT_F_ESCAPING_THE_GASLIGHTER},
    }

    # The version is passed from main.py, which randomly selects 'a'-'f'.
    version_to_use = version
    if version not in strategy_map:
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