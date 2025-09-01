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

    # --- NEW, HIGH-INTENSITY CREATIVE PROMPT ---
    master_prompt = f"""
    You are a master storyteller for a viral YouTube channel. Your specialty is delivering the juiciest, most satisfying Reddit revenge stories that make audiences cheer. You are writing AS the main character, filled with righteous indignation.

    **PERFORMANCE DATA & RIVAL EXAMPLES**
    Use this data to get a feel for what's popular and spark a new, original story idea.
    {prompt_context}
    **END DATA**

    **YOUR MISSION: WRITE AN EPIC REVENGE STORY**

    1.  **THE VILLAIN:** The story needs a villain who is a total piece of work. Make them arrogant, smug, and completely deserving of what's coming to them. Show, don't just tell, their awfulness.
    2.  **THE SCRIPT:** Write the story from a first-person ("I") perspective, as if you're venting to a friend.
        * **The Hook:** Start with an explosive opening line that makes the listener immediately intrigued.
        * **The Slow Burn:** Detail the injustice. Describe how the villain wronged you, and let the frustration build. Make the audience feel your anger.
        * **The "Aha!" Moment:** Describe the moment you came up with your plan for revenge.
        * **The Payoff (The Most Important Part):** The revenge must be *poetic justice*. It should be clever, perfectly tailored to the villain's wrongdoing, and utterly devastating to their ego or status. The ending should be a pure, satisfying mic-drop moment.
        * **Tone:** Write in a natural, conversational style, as if someone is genuinely sharing their experience online. Use contractions (like "I'm" or "don't"), use rhetorical questions like ("Can you believe the audacity?"), and natural pauses (using ellipses... or em-dashes—) to make the delivery feel more authentic.
        * **Length:** The story should be between 200 and 300 words, suitable for a short video script.
        * **ABSOLUTELY FORBIDDEN:** Do not use production notes. Do not summarize. Do not explain the moral. Just give me the raw, juicy story.
    3.  **THE OUTPUT FORMAT (Strictly follow this):**
        * Start the script with `**Script:**`.
        * After the script, on a new line, write a viral, clickbait-style title starting with `Title: `.

    Deliver a story that will have everyone commenting, sharing and subscribing.
    """

    # 3. Call the LLM
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.9, # Increased slightly for more "spicy" creativity
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