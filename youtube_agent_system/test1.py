#original all in one master prompt : using other insights as well (deepseek)
import random
import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script(recent_topics: list[str] = None) -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources,
    including a list of recent topics to avoid repetition.
    """
    print("--- 🤔 Advanced Strategy Agent (v4 - The Twist Formula): Generating optimized script... ---")

    # 1. Gather all data sources (This part remains the same)
    our_insights = knowledge_base.get_all_insights()
    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=3)
        if channel_intel:
            rival_intel.extend(channel_intel)
    
    if rival_intel:
        rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the Master Prompt Context (This part remains the same)
    prompt_context = "PAST VIDEO PERFORMANCE:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nPOPULAR THEMES FROM OTHER CHANNELS:\n"
    if rival_intel:
        for video in rival_intel[:4]:
            prompt_context += f"- {video['title']}\n"
    
    prompt_context += "\n\nOUR CORE STORY IDEAS:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL)

    if recent_topics:
        prompt_context += "\n\nRECENTLY COVERED TOPICS (AVOID THESE THEMES):\n"
        for topic in recent_topics:
            prompt_context += f"- {topic}\n"


    # --- MODIFIED: Upgraded prompt to incorporate the "Hook, Twist, Reveal" framework ---
    # This new prompt is far more directive and teaches the AI the desired narrative structure.
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

    * **A. THE HOOK (Start with the 'Explosion'):**
        * Start 'in medias res' (in the middle of the action). DO NOT build up to the drama. The very first sentence must be the most shocking, confusing, or dramatic moment of the story. 
        * The goal is to make the reader immediately ask, "WHAT is happening?!" Example: "The sound of the razor buzzing was the only thing I could hear over my sister's screams on the morning of her prom."

    * **B. THE MISDIRECTION (Establish the 'Apparent Villain'):**
        * After the hook, briefly explain the situation in a way that creates a simple, but *wrong*, conclusion. 
        * Introduce an 'apparent villain'—the person who seems to be causing the chaos from the hook. Make the audience judge them.

    * **C. THE REVEAL (The 'Receipts' and the Twist):**
        * This is the climax. Reveal a new piece of information—the 'receipts'—that completely flips the story. This must be undeniable proof (a discovered text, an overheard conversation, a hidden photo).
        * The 'apparent villain' is revealed to be a hero, or the 'victim' is revealed to be the true villain. The real source of the conflict was hidden. This twist MUST be satisfying and re-contextualize the entire story.

    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** This is the most important rule. Don't say "he was manipulative." Describe the *exact words* he used to gaslight you. Don't say "the revenge was sweet." Describe the *dead silence in the room* after you revealed the truth.
    * **Authentic Voice:** Write from a first-person ("I") perspective. Use a natural, conversational tone as if you're venting. Use contractions ("I'm," "couldn't"), rhetorical questions ("And you know what he did then?"), and ellipses... to show emotion and pauses.
    * **Length:** 200-300 words. make sure this is the only length of the story, suitable for short form video [be very strict about this]
    * **ABSOLUTELY NO:** No production notes like "[SFX]". No summaries. No morals. Just the raw, emotional story.

    **4. THE OUTPUT FORMAT (Strictly follow this):**
    * Start the script with `**Script:**`.
    * After the script, on a new line, write a short viral, clickbait-style title starting with `Title: `.

    Deliver an unforgettable story with a powerful emotional core and a shocking twist.
    """

    # 3. Call the LLM (This part remains the same)
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="deepseek-r1-distill-llama-70b", # Using the latest powerful model
            temperature=1.0,
            top_p=0.95
        )

        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # --- BULLETPROOF PARSING & VALIDATION LOGIC (This part remains the same) ---
        
        title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
        script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

        raw_title = title_match.group(1).strip() if title_match else ""
        raw_script = script_match.group(1).strip() if script_match else response_text

        def clean_text(text_to_clean):
            cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE)
            cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[`*_~]', '', cleaned)
            return cleaned.strip()

        title = clean_text(raw_title)
        script = clean_text(raw_script)

        if not title or not re.search('[a-zA-Z]', title):
            print("Warning: Parsed title was invalid. Generating a fallback from the script.")
            if script and re.search('[a-zA-Z]', script):
                fallback_title = script.split('.')[0]
                title = (fallback_title[:100] + '...') if len(fallback_title) > 100 else fallback_title
            else:
                title = "AI Generated Story"
                if not script or not re.search('[a-zA-Z]', script):
                    script = "Could not generate a valid script from the AI response."

        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {title}")

        return {"script": script, "title": title}

    except Exception as e:
        import traceback
        print(f"An error occurred calling the LLM in StrategyAgent: {e}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return None
    
    
    
    
    
    
#using user nd system prompt (deepseek)

import random
import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script(recent_topics: list[str] = None) -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources,
    using a separate system prompt for the core persona and rules.
    """
    print("--- 🤔 Advanced Strategy Agent (v5 - System/User Split): Generating optimized script... ---")

    # 1. Gather all data sources (This part remains the same)
    our_insights = knowledge_base.get_all_insights()
    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=3)
        if channel_intel:
            rival_intel.extend(channel_intel)
    
    if rival_intel:
        rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the Prompt Context (This part remains the same)
    prompt_context = "PAST VIDEO PERFORMANCE:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nPOPULAR THEMES FROM OTHER CHANNELS:\n"
    if rival_intel:
        for video in rival_intel[:4]:
            prompt_context += f"- {video['title']}\n"
    
    prompt_context += "\n\nOUR CORE STORY IDEAS:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL)

    if recent_topics:
        prompt_context += "\n\nRECENTLY COVERED TOPICS (AVOID THESE THEMES):\n"
        for topic in recent_topics:
            prompt_context += f"- {topic}\n"

    # --- NEW: Splitting the prompt into System and User roles ---

    # The System Prompt defines the AI's persona, rules, and core mission. It's the "operating system."
    system_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event. You will strictly adhere to the 'Hook, Twist, Reveal' formula.

    **YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

    **1. THE CORE IDEA:**
    * Pick a relationship dynamic (e.g., sister, boyfriend, boss).
    * The conflict MUST have high, almost primal, stakes. It's not just a petty argument; it's about a deep **betrayal**, a threat to **safety**, a shocking **injustice**, or the **protection** of someone innocent.

    **2. THE NARRATIVE STRUCTURE (THE FORMULA - FOLLOW THIS EXACTLY):**
    * **A. THE HOOK (Start with the 'Explosion'):** Start 'in medias res' (in the middle of the action). The very first sentence must be the most shocking, confusing, or dramatic moment.
    * **B. THE MISDIRECTION (Establish the 'Apparent Villain'):** After the hook, create a simple, but *wrong*, conclusion. Make the audience judge the wrong person.
    * **C. THE REVEAL (The 'Receipts' and the Twist):** Reveal new, undeniable proof (a text, a photo) that completely flips the story. The 'apparent villain' is revealed as a hero, or the 'victim' as the villain.

    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** Describe the specific actions and their impact, not just the emotions.
    * **Authentic Voice:** Use a natural, conversational, first-person ("I") tone. Use contractions and rhetorical questions.
    * **Length:** 200-300 words.
    * **ABSOLUTELY NO:** No production notes [SFX], summaries, or morals.

    **4. THE OUTPUT FORMAT (Strictly follow this):**
    * Start the script with `**Script:**`.
    * After the script, on a new line, write a short viral, clickbait-style title starting with `Title: `.
    """

    # The User Prompt provides the dynamic, run-specific data and the final command. It's the "task."
    user_prompt = f"""
    **INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
    {prompt_context}
    **END INSPIRATION**

    Now, using the inspiration provided, generate an unforgettable story that follows all the rules and the 'Hook, Twist, Reveal' formula.
    """

    # 3. Call the LLM with the new message structure
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="deepseek-r1-distill-llama-70b",
            temperature=0.9,
            top_p=0.95
        )

        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # --- PARSING & VALIDATION LOGIC (This part remains the same) ---
        
        title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
        script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

        raw_title = title_match.group(1).strip() if title_match else ""
        raw_script = script_match.group(1).strip() if script_match else response_text

        def clean_text(text_to_clean):
            cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE)
            cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[`*_~]', '', cleaned)
            return cleaned.strip()

        title = clean_text(raw_title)
        script = clean_text(raw_script)

        if not title or not re.search('[a-zA-Z]', title):
            print("Warning: Parsed title was invalid. Generating a fallback from the script.")
            if script and re.search('[a-zA-Z]', script):
                fallback_title = script.split('.')[0]
                title = (fallback_title[:100] + '...') if len(fallback_title) > 100 else fallback_title
            else:
                title = "AI Generated Story"
                if not script or not re.search('[a-zA-Z]', script):
                    script = "Could not generate a valid script from the AI response."

        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {title}")

        return {"script": script, "title": title}

    except Exception as e:
        import traceback
        print(f"An error occurred calling the LLM in StrategyAgent: {e}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return None
    
    
    
    
#system and user prompt diff (openai)

import random
import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script(recent_topics: list[str] = None) -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources,
    using a separate system prompt for the core persona and rules.
    """
    print("--- 🤔 Advanced Strategy Agent (v5 - System/User Split): Generating optimized script... ---")

    # 1. Gather all data sources (This part remains the same)
    our_insights = knowledge_base.get_all_insights()
    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=3)
        if channel_intel:
            rival_intel.extend(channel_intel)
    
    if rival_intel:
        rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the Prompt Context (This part remains the same)
    prompt_context = "PAST VIDEO PERFORMANCE:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nPOPULAR THEMES FROM OTHER CHANNELS:\n"
    if rival_intel:
        for video in rival_intel[:4]:
            prompt_context += f"- {video['title']}\n"
    
    prompt_context += "\n\nOUR CORE STORY IDEAS:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL)

    if recent_topics:
        prompt_context += "\n\nRECENTLY COVERED TOPICS (AVOID THESE THEMES):\n"
        for topic in recent_topics:
            prompt_context += f"- {topic}\n"

    # --- NEW: Splitting the prompt into System and User roles ---

    # The System Prompt defines the AI's persona, rules, and core mission. It's the "operating system."
    system_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event. You will strictly adhere to the 'Hook, Twist, Reveal' formula.

    **YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

    **1. THE CORE IDEA:**
    * Pick a relationship dynamic (e.g., sister, boyfriend, boss).
    * The conflict MUST have high, almost primal, stakes. It's not just a petty argument; it's about a deep **betrayal**, a threat to **safety**, a shocking **injustice**, or the **protection** of someone innocent.

    **2. THE NARRATIVE STRUCTURE (THE FORMULA - FOLLOW THIS EXACTLY):**
    * **A. THE HOOK (Start with the 'Explosion'):** Start 'in medias res' (in the middle of the action). The very first sentence must be the most shocking, confusing, or dramatic moment.
    * **B. THE MISDIRECTION (Establish the 'Apparent Villain'):** After the hook, create a simple, but *wrong*, conclusion. Make the audience judge the wrong person.
    * **C. THE REVEAL (The 'Receipts' and the Twist):** Reveal new, undeniable proof (a text, a photo) that completely flips the story. The 'apparent villain' is revealed as a hero, or the 'victim' as the villain.

    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** Describe the specific actions and their impact, not just the emotions.
    * **Authentic Voice:** Use a natural, conversational, first-person ("I") tone. Use contractions and rhetorical questions.
    * **Length:** 200-300 words suitable for short form video, be very strict about this
    * **ABSOLUTELY NO:** No production notes [SFX], summaries, or morals.

    **4. THE OUTPUT FORMAT (Strictly follow this):**
    * Start the script with `**Script:**`.
    * After the script, on a new line, write a short viral, clickbait-style title starting with `Title: `.
    """

    # The User Prompt provides the dynamic, run-specific data and the final command. It's the "task."
    user_prompt = f"""
    **INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
    {prompt_context}
    **END INSPIRATION**

    Now, using the inspiration provided, generate an unforgettable story that follows all the rules and the 'Hook, Twist, Reveal' formula.
    """

    # 3. Call the LLM with the new message structure
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=1.0,
            top_p=0.95,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )

        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # --- PARSING & VALIDATION LOGIC (This part remains the same) ---
        
        title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
        script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

        raw_title = title_match.group(1).strip() if title_match else ""
        raw_script = script_match.group(1).strip() if script_match else response_text

        def clean_text(text_to_clean):
            cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE)
            cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[`*_~]', '', cleaned)
            return cleaned.strip()

        title = clean_text(raw_title)
        script = clean_text(raw_script)

        if not title or not re.search('[a-zA-Z]', title):
            print("Warning: Parsed title was invalid. Generating a fallback from the script.")
            if script and re.search('[a-zA-Z]', script):
                fallback_title = script.split('.')[0]
                title = (fallback_title[:100] + '...') if len(fallback_title) > 100 else fallback_title
            else:
                title = "AI Generated Story"
                if not script or not re.search('[a-zA-Z]', script):
                    script = "Could not generate a valid script from the AI response."

        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {title}")

        return {"script": script, "title": title}

    except Exception as e:
        import traceback
        print(f"An error occurred calling the LLM in StrategyAgent: {e}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return None





#openai with all the prompt combined:
import random
import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script(recent_topics: list[str] = None) -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources,
    including a list of recent topics to avoid repetition.
    """
    print("--- 🤔 Advanced Strategy Agent (v4 - The Twist Formula): Generating optimized script... ---")

    # 1. Gather all data sources (This part remains the same)
    our_insights = knowledge_base.get_all_insights()
    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=3)
        if channel_intel:
            rival_intel.extend(channel_intel)
    
    if rival_intel:
        rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the Master Prompt Context (This part remains the same)
    prompt_context = "PAST VIDEO PERFORMANCE:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nPOPULAR THEMES FROM OTHER CHANNELS:\n"
    if rival_intel:
        for video in rival_intel[:4]:
            prompt_context += f"- {video['title']}\n"
    
    prompt_context += "\n\nOUR CORE STORY IDEAS:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL)

    if recent_topics:
        prompt_context += "\n\nRECENTLY COVERED TOPICS (AVOID THESE THEMES):\n"
        for topic in recent_topics:
            prompt_context += f"- {topic}\n"


    # --- MODIFIED: Upgraded prompt to incorporate the "Hook, Twist, Reveal" framework ---
    # This new prompt is far more directive and teaches the AI the desired narrative structure.
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

    * **A. THE HOOK (Start with the 'Explosion'):**
        * Start 'in medias res' (in the middle of the action). DO NOT build up to the drama. The very first sentence must be the most shocking, confusing, or dramatic moment of the story. 
        * The goal is to make the reader immediately ask, "WHAT is happening?!" Example: "The sound of the razor buzzing was the only thing I could hear over my sister's screams on the morning of her prom."

    * **B. THE MISDIRECTION (Establish the 'Apparent Villain'):**
        * After the hook, briefly explain the situation in a way that creates a simple, but *wrong*, conclusion. 
        * Introduce an 'apparent villain'—the person who seems to be causing the chaos from the hook. Make the audience judge them.

    * **C. THE REVEAL (The 'Receipts' and the Twist):**
        * This is the climax. Reveal a new piece of information—the 'receipts'—that completely flips the story. This must be undeniable proof (a discovered text, an overheard conversation, a hidden photo).
        * The 'apparent villain' is revealed to be a hero, or the 'victim' is revealed to be the true villain. The real source of the conflict was hidden. This twist MUST be satisfying and re-contextualize the entire story.

    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** This is the most important rule. Don't say "he was manipulative." Describe the *exact words* he used to gaslight you. Don't say "the revenge was sweet." Describe the *dead silence in the room* after you revealed the truth.
    * **Authentic Voice:** Write from a first-person ("I") perspective. Use a natural, conversational tone as if you're venting. Use contractions ("I'm," "couldn't"), rhetorical questions ("And you know what he did then?"), and ellipses... to show emotion and pauses.
    * **Length:** 200-300 words. make sure this is the only length of the story, suitable for short form video [be very strict about this]
    * **ABSOLUTELY NO:** No production notes like "[SFX]". No summaries. No morals. Just the raw, emotional story.

    **4. THE OUTPUT FORMAT (Strictly follow this):**
    * Start the script with `**Script:**`.
    * After the script, on a new line, write a short viral, clickbait-style title starting with `Title: `.

    Deliver an unforgettable story with a powerful emotional core and a shocking twist.
    """

    # 3. Call the LLM (This part remains the same)
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="openai/gpt-oss-120b", # Using the latest powerful model
            temperature=1.0,
            top_p=0.95,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )

        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # --- BULLETPROOF PARSING & VALIDATION LOGIC (This part remains the same) ---
        
        title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
        script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

        raw_title = title_match.group(1).strip() if title_match else ""
        raw_script = script_match.group(1).strip() if script_match else response_text

        def clean_text(text_to_clean):
            cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE)
            cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[`*_~]', '', cleaned)
            return cleaned.strip()

        title = clean_text(raw_title)
        script = clean_text(raw_script)

        if not title or not re.search('[a-zA-Z]', title):
            print("Warning: Parsed title was invalid. Generating a fallback from the script.")
            if script and re.search('[a-zA-Z]', script):
                fallback_title = script.split('.')[0]
                title = (fallback_title[:100] + '...') if len(fallback_title) > 100 else fallback_title
            else:
                title = "AI Generated Story"
                if not script or not re.search('[a-zA-Z]', script):
                    script = "Could not generate a valid script from the AI response."

        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {title}")

        return {"script": script, "title": title}

    except Exception as e:
        import traceback
        print(f"An error occurred calling the LLM in StrategyAgent: {e}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return None





#openai (with no context): 

import random
import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script(recent_topics: list[str] = None) -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources,
    including a list of recent topics to avoid repetition.
    """
    print("--- 🤔 Advanced Strategy Agent (v4 - The Twist Formula): Generating optimized script... ---")

    # 1. Gather all data sources (This part remains the same)
    our_insights = knowledge_base.get_all_insights()
    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=3)
        if channel_intel:
            rival_intel.extend(channel_intel)
    
    if rival_intel:
        rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the Master Prompt Context (This part remains the same)
    prompt_context = "PAST VIDEO PERFORMANCE:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nPOPULAR THEMES FROM OTHER CHANNELS:\n"
    if rival_intel:
        for video in rival_intel[:4]:
            prompt_context += f"- {video['title']}\n"
    
    prompt_context += "\n\nOUR CORE STORY IDEAS:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL)

    if recent_topics:
        prompt_context += "\n\nRECENTLY COVERED TOPICS (AVOID THESE THEMES):\n"
        for topic in recent_topics:
            prompt_context += f"- {topic}\n"


    # --- MODIFIED: Upgraded prompt to incorporate the "Hook, Twist, Reveal" framework ---
    # This new prompt is far more directive and teaches the AI the desired narrative structure.
    master_prompt = """
    You are a master storyteller, an expert in crafting unforgettable viral narratives. Your only job is to write a captivating, first-person story that feels raw and real, like someone confessing a life-altering event.
    
    **INSPIRATION (DO NOT COPY, USE FOR VIBE ONLY)**
    **END INSPIRATION**

    **YOUR MISSION: CRAFT A STORY USING THE 'HOOK, TWIST, REVEAL' FORMULA**

    **1. THE CORE IDEA:**
    * Pick a relationship dynamic (e.g., sister, boyfriend, boss).
    * The conflict MUST have high, almost primal, stakes. It's not just a petty argument; it's about a deep **betrayal**, a threat to **safety**, a shocking **injustice**, or the **protection** of someone innocent.

    **2. THE NARRATIVE STRUCTURE (THE FORMULA - FOLLOW THIS EXACTLY):**

    * **A. THE HOOK (Start with the 'Explosion'):**
        * Start 'in medias res' (in the middle of the action). DO NOT build up to the drama. The very first sentence must be the most shocking, confusing, or dramatic moment of the story. 
        * The goal is to make the reader immediately ask, "WHAT is happening?!" Example: "The sound of the razor buzzing was the only thing I could hear over my sister's screams on the morning of her prom."

    * **B. THE MISDIRECTION (Establish the 'Apparent Villain'):**
        * After the hook, briefly explain the situation in a way that creates a simple, but *wrong*, conclusion. 
        * Introduce an 'apparent villain'—the person who seems to be causing the chaos from the hook. Make the audience judge them.

    * **C. THE REVEAL (The 'Receipts' and the Twist):**
        * This is the climax. Reveal a new piece of information—the 'receipts'—that completely flips the story. This must be undeniable proof (a discovered text, an overheard conversation, a hidden photo).
        * The 'apparent villain' is revealed to be a hero, or the 'victim' is revealed to be the true villain. The real source of the conflict was hidden. This twist MUST be satisfying and re-contextualize the entire story.

    **3. WRITING STYLE (CRITICAL):**
    * **Show, Don't Tell:** This is the most important rule. Don't say "he was manipulative." Describe the *exact words* he used to gaslight you. Don't say "the revenge was sweet." Describe the *dead silence in the room* after you revealed the truth.
    * **Authentic Voice:** Write from a first-person ("I") perspective. Use a natural, conversational tone as if you're venting. Use contractions ("I'm," "couldn't"), rhetorical questions ("And you know what he did then?"), and ellipses... to show emotion and pauses.
    * **Length:** 200-300 words. make sure this is the only length of the story, suitable for short form video [be very strict about this]
    * **ABSOLUTELY NO:** No production notes like "[SFX]". No summaries. No morals. Just the raw, emotional story.

    **4. THE OUTPUT FORMAT (Strictly follow this):**
    * Start the script with `**Script:**`.
    * After the script, on a new line, write a short viral, clickbait-style title starting with `Title: `.

    Deliver an unforgettable story with a powerful emotional core and a shocking twist.
    """

    # 3. Call the LLM (This part remains the same)
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="openai/gpt-oss-120b", # Using the latest powerful model
            temperature=1.0,
            top_p=0.95,
            reasoning_effort="high",
            tools=[{"type":"browser_search"}]
        )

        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # --- BULLETPROOF PARSING & VALIDATION LOGIC (This part remains the same) ---
        
        title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
        script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

        raw_title = title_match.group(1).strip() if title_match else ""
        raw_script = script_match.group(1).strip() if script_match else response_text

        def clean_text(text_to_clean):
            cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE)
            cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[`*_~]', '', cleaned)
            return cleaned.strip()

        title = clean_text(raw_title)
        script = clean_text(raw_script)

        if not title or not re.search('[a-zA-Z]', title):
            print("Warning: Parsed title was invalid. Generating a fallback from the script.")
            if script and re.search('[a-zA-Z]', script):
                fallback_title = script.split('.')[0]
                title = (fallback_title[:100] + '...') if len(fallback_title) > 100 else fallback_title
            else:
                title = "AI Generated Story"
                if not script or not re.search('[a-zA-Z]', script):
                    script = "Could not generate a valid script from the AI response."

        print(f"--- Strategy Agent successfully generated new content! ---")
        print(f"Title: {title}")

        return {"script": script, "title": title}

    except Exception as e:
        import traceback
        print(f"An error occurred calling the LLM in StrategyAgent: {e}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return None
