import random
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

def generate_optimized_script() -> dict | None:
    """
    Generates a new, optimized script by synthesizing multiple data sources.

    This is the new "brain" of the operation. It gathers intel, constructs
    a "master prompt", and uses an LLM to generate a complete script and title.

    Returns:
        A dictionary containing the 'script' and 'title', or None on failure.
    """
    print("--- 🤔 Advanced Strategy Agent (v3): Generating optimized script... ---")

    # 1. Gather all data sources
    our_insights = knowledge_base.get_all_insights()

    rival_intel = []
    for channel_url in config.RIVAL_CHANNEL_URLS:
        channel_intel = rival_scanner.get_channel_shorts_info(channel_url, playlist_end=5)
        if channel_intel:
            rival_intel.extend(channel_intel)

    # Sort rival intel by views to find the best performers
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

    prompt_context += "\nOur general content style is similar to these topics:\n"
    prompt_context += "\n".join(f"- {topic}" for topic in config.STATIC_TOPIC_POOL[:2])


    master_prompt = f"""
    You are an expert YouTube content strategist and scriptwriter for a viral 'Reddit Stories' channel.
    Your task is to synthesize all of the provided data to create one new, viral video script.

    **[CONTEXT]**
    {prompt_context}
    **[END CONTEXT]**

    **Your Task:**
    1.  **Analyze:** Briefly analyze the context above.
    2.  **Synthesize & Generate:** Based on your analysis, create a single, new, original story idea.
    3.  **Write Script:** Write the complete, ready-to-produce script for this new story. The script must be 200-300 words and written in a compelling, first-person narrative style. **You must begin the script with the marker `**Script:**`.**
    4.  **Provide Title:** At the very end of your response, on a completely new line, provide a compelling and clickable title for this new story. The title must be prefixed with "Title: ".

    Generate the script now.
    """

    # 3. Call the LLM
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
        )

        # CRITICAL FIX: Add a safety check to ensure the LLM returned a response
        if not chat_completion.choices:
            print("Error: The AI model returned an empty response.")
            return None

        response_text = chat_completion.choices[0].message.content.strip()

        # 4. More robustly parse the output
        if "**Script:**" in response_text and "Title:" in response_text:
            script_part = response_text.split("**Script:**", 1)[1]
            script = script_part.rsplit("\nTitle:", 1)[0].strip()
            title = response_text.rsplit("\nTitle:", 1)[1].strip()

            print(f"--- Strategy Agent successfully generated new content! ---")
            print(f"Title: {title}")

            return {"script": script, "title": title}
        else:
            print("Warning: LLM did not provide a title in the expected format. Using the full response as script.")
            return {"script": response_text, "title": "AI Generated Story"}

    except Exception as e:
        print(f"An error occurred calling the LLM in StrategyAgent: {e}")
        return None

if __name__ == '__main__':
    print("--- Testing Advanced Strategy Agent ---")
    knowledge_base.save_insight(
        "dummy_id_test",
        "Video 'AITA for leaving my own party' performed well with 25k views.",
        {"topic": "AITA for leaving my own party", "views": 25000}
    )

    result = generate_optimized_script()
    if result:
        print("\n--- Generation Complete ---")
        print(f"Title: {result['title']}")
        print(f"Script preview: {result['script'][:150]}...")
    else:
        print("\n--- Generation Failed ---")
