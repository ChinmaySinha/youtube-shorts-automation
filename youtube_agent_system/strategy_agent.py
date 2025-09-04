import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

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

# --- STRATEGY VERSION A ---
def _generate_script_v_a(prompt_context: str) -> dict | None:
    print("--- Running Strategy Version A (DeepSeek All-In-One) ---")
    master_prompt = f"""
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
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="deepseek-r1-distill-llama-70b",
            temperature=1.0,
            top_p=0.95
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in Strategy A: {e}")
        traceback.print_exc()
        return None

# --- STRATEGY VERSION B ---
def _generate_script_v_b(prompt_context: str) -> dict | None:
    print("--- Running Strategy Version B (DeepSeek System/User Split) ---")
    system_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event. You will strictly adhere to the 'Hook, Twist, Reveal' formula.

    **YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

    **1. THE CORE IDEA:** High stakes relationship conflict (betrayal, safety, injustice).
    **2. THE NARRATIVE STRUCTURE (FOLLOW EXACTLY):**
    * **A. THE HOOK:** Start 'in medias res' with the most dramatic moment.
    * **B. THE MISDIRECTION:** Create a wrong conclusion; establish an 'apparent villain'.
    * **C. THE REVEAL:** Reveal undeniable proof (receipts) that flips the entire story.
    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** Describe specific actions and their impact, not just emotions.
    * **Authentic Voice:** Use a natural, conversational, first-person ("I") tone. The story should be easy to follow.
    * **Length:** 200-300 words. Be very strict about this.
    * **ABSOLUTELY NO:** No production notes like "[SFX]". No summaries. No morals.
    **4. OUTPUT FORMAT:** Start with `**Script:**`. After the script, on a new line, write `Title: `. (Strictly follow this.)
    """
    user_prompt = f"""
    **INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
    {prompt_context}
    **END INSPIRATION**

    Now, using the inspiration provided, generate an unforgettable story that follows all the rules and the 'Hook, Twist, Reveal' formula.
    """
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="deepseek-r1-distill-llama-70b",
            temperature=1.0,
            top_p=0.95
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in Strategy B: {e}")
        traceback.print_exc()
        return None

# --- STRATEGY VERSION C ---
def _generate_script_v_c(prompt_context: str) -> dict | None:
    print("--- Running Strategy Version C (OpenAI System/User Split) ---")
    # This is identical to B, but points to a different conceptual model
    system_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event. You will strictly adhere to the 'Hook, Twist, Reveal' formula.

    **YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

    **1. THE CORE IDEA:** High stakes relationship conflict (betrayal, safety, injustice).
    **2. THE NARRATIVE STRUCTURE (FOLLOW EXACTLY):**
    * **A. THE HOOK:** Start 'in medias res' with the most dramatic moment.
    * **B. THE MISDIRECTION:** Create a wrong conclusion; establish an 'apparent villain'.
    * **C. THE REVEAL:** Reveal undeniable proof (receipts) that flips the entire story.
    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** Describe specific actions and their impact, not just emotions.
    * **Authentic Voice:** Use a natural, conversational, first-person ("I") tone. The story should be easy to follow.
    * **Length:** 200-300 words. Be very strict about this.
    * **ABSOLUTELY NO:** No production notes like "[SFX]". No summaries. No morals.
    **4. OUTPUT FORMAT:** Start with `**Script:**`. After the script, on a new line, write `Title: `. (Strictly follow this)
    """
    user_prompt = f"""
    **INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
    {prompt_context}
    **END INSPIRATION**

    Now, using the inspiration provided, generate an unforgettable story that follows all the rules and the 'Hook, Twist, Reveal' formula.
    """
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="openai/gpt-oss-120b", # Different model for variety
            temperature=1.0,
            top_p=1,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in Strategy C: {e}")
        traceback.print_exc()
        return None

# --- STRATEGY VERSION D ---
def _generate_script_v_d(prompt_context: str) -> dict | None:
    print("--- Running Strategy Version D (OpenAI All-In-One) ---")
    # This is identical to A, but points to a different conceptual model
    master_prompt = f"""
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
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="openai/gpt-oss-120b", # Different model for variety
            temperature=1.0,
            top_p=1,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in Strategy D: {e}")
        traceback.print_exc()
        return None

# --- STRATEGY VERSION E ---
def _generate_script_v_e(prompt_context: str) -> dict | None:
    print("--- Running Strategy Version E (OpenAI with No Context) ---")
    # This version intentionally ignores the provided context for maximum creativity.
    master_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event.
    
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
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="openai/gpt-oss-120b", # Using a powerful model for creativity
            temperature=1.0, # Higher temperature for more variance
            top_p=1,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in Strategy E: {e}")
        traceback.print_exc()
        return None

# --- STRATEGY VERSION F ---
def _generate_script_v_f(prompt_context: str) -> dict | None:
    print("--- Running Strategy Version F (DeepSeek with No Context) ---")
    # This version is identical to E, but uses the other model family.
    master_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event.
    
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
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="deepseek-r1-distill-llama-70b",
            temperature=1.0,
            top_p=0.95
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return _clean_and_parse_response(response_text)
    except Exception as e:
        import traceback
        print(f"An error occurred in Strategy F: {e}")
        traceback.print_exc()
        return None


# --- MAIN DISPATCHER FUNCTION ---
def generate_optimized_script(recent_topics: list[str] = None, version: str = 'a') -> dict | None:
    """
    Selects a strategy version, generates a script, and returns the result.
    This is the single entry point called by main.py.
    """
    print("--- 🤔 Advanced Strategy Agent: Generating optimized script... ---")

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
    version_map = {
        'a': _generate_script_v_a,
        'b': _generate_script_v_b,
        'c': _generate_script_v_c,
        'd': _generate_script_v_d,
        'e': _generate_script_v_e,
        'f': _generate_script_v_f,
    }

    strategy_function = version_map.get(version)
    if not strategy_function:
        print(f"Error: Invalid strategy version '{version}'. Defaulting to 'a'.")
        strategy_function = _generate_script_v_a

    # 4. Execute the strategy and get the final result
    result = strategy_function(prompt_context)
    
    if result:
        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {result['title']}")
        return result
    else:
        print(f"--- Strategy '{version.upper()}' failed to generate content. ---")
        return None