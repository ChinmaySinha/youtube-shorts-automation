import random
import re
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script() -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources.
    """
    print("--- 🤔 Advanced Strategy Agent (v3): Generating optimized script... ---")

    # 1. Gather all data sources
    our_insights = knowledge_base.get_all_insights()

    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=5)
        if channel_intel:
            rival_intel.extend(channel_intel)

    rival_intel.sort(key=lambda x: x['views'], reverse=True)

    # 2. Construct the Master Prompt
    prompt_context = "Here is the performance of our past videos:\n"
    if our_insights:
        prompt_context += "\n".join(our_insights)
    else:
        prompt_context += "No data from our past videos is available yet.\n"

    prompt_context += "\n\nHere are the top-performing recent videos from a rival channel:\n"
    if rival_intel:
        for video in rival_intel[:3]: # Use top 3 for brevity
            prompt_context += f"- Title: {video['title']} ({video['views']} views)\n"
    else:
        prompt_context += "No data from rival channels is available.\n"

    # --- RESTORED HIGH-QUALITY STORYTELLING PROMPT ---
    master_prompt = f"""
    You are a skilled writer who specializes in creating dramatic, first-person Reddit-style stories (like AITA, ProRevenge, etc.).
    Your primary goal is to write a compelling, human-like story based on the ideas you gather from the context provided.

    **[CONTEXT FOR INSPIRATION ONLY]**
    {prompt_context}
    **[END CONTEXT]**

    **YOUR TASK:**
    1.  **Get an Idea:** Briefly look at the context to get an idea for a new, original story.
    2.  **Write the Story Script:** Now, write the full story. You MUST follow these creative rules:
        * **First-Person Narrative:** Write the entire story from the "I" perspective.
        * **Conversational Tone:** Write in a natural, conversational style, as if someone is genuinely sharing their experience online.
        * **Story Structure:** The story must have a clear beginning (setup), a middle (conflict), and an end (a satisfying resolution or revenge).
        * **Word Count:** The story should be between 200 and 300 words.
        * **Dramatic and Engaging:** Build suspense and emotion. Make the conflict compelling.
        * **WHAT TO AVOID:** Do NOT write summaries, production notes like "[SFX]", or be preachy. Just tell the story.
    3.  **Provide Final Output:** Your entire response must follow this exact format:
        * The script must begin with the marker `**Script:**`.
        * After the script, on a completely new line, provide a compelling, clickable title for the video, prefixed with `Title: `.

    Generate the high-quality story now.
    """

    # 3. Call the LLM
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="llama-3.3-70b-versatile", # <-- UPDATED MODEL
            temperature=0.8,
        )

        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # --- BULLETPROOF PARSING & VALIDATION LOGIC ---
        
        # Step 1: Extract raw text for title and script
        title_match = re.search(r'Title:\s*(.*)', response_text, re.IGNORECASE)
        script_match = re.search(r'\*\*?Script:\*\*?(.*)', response_text, re.DOTALL | re.IGNORECASE)

        raw_title = title_match.group(1).strip() if title_match else ""
        raw_script = script_match.group(1).strip() if script_match else response_text

        # Step 2: Aggressively clean the extracted text
        def clean_text(text_to_clean):
            cleaned = re.sub(r'Title:\s*.*', '', text_to_clean, flags=re.IGNORECASE)
            cleaned = re.sub(r'\*\*?Script:\*\*?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[`*_~]', '', cleaned)
            return cleaned.strip()

        title = clean_text(raw_title)
        script = clean_text(raw_script)

        # Step 3: Validate the cleaned text and create fallbacks if needed
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