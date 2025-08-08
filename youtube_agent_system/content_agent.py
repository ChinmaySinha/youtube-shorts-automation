import os
from groq import Groq
from . import config

def generate_story_script(topic: str) -> str:
    """
    Generates a compelling, human-like story script using an LLM.

    This function embodies the ContentAgent's role. It takes a topic,
    constructs a sophisticated prompt based on storytelling best practices,
    and gets a story from the Groq API.

    Args:
        topic: The central theme or topic for the story.

    Returns:
        A string containing the generated story script.
        Returns an error message if the API key is not configured.
    """
    if not config.GROQ_API_KEY:
        return "Error: GROQ_API_KEY is not configured in the .env file."

    client = Groq(api_key=config.GROQ_API_KEY)

    # This prompt is engineered based on the principles in the blueprint.
    # It sets a persona, provides clear instructions, and includes negative constraints.
    prompt = f"""
    You are a master storyteller, known for crafting short, deeply engaging, and emotionally resonant narratives.
    Your task is to write a story based on the following topic: "{topic}".

    **Instructions & Constraints:**
    1.  **Narrative Arc:** The story must have a clear beginning, a rising action, a climax, and a brief, impactful resolution.
    2.  **Show, Don't Tell:** Do not state emotions directly (e.g., "he was sad"). Instead, describe actions, thoughts, and dialogue that convey the emotion (e.g., "his shoulders slumped, the world a grey blur").
    3.  **Sentence Structure:** Vary your sentence structure. Use a mix of short, punchy sentences for impact and longer, descriptive sentences for setting the scene.
    4.  **Word Count:** The entire story should be between 150 and 250 words. This is for a short video.
    5.  **Tone:** The tone should be slightly melancholic but hopeful.

    **Negative Constraints (What to AVOID):**
    -   Do not use clichés or overused phrases (e.g., "in the nick of time," "a storm was brewing," "their eyes widened in surprise").
    -   Do not start the story with "Once upon a time."
    -   Do not end the story with a cheesy moral or a summary of the events. Let the story speak for itself.
    -   Do not use filler words or sentences that don't advance the plot or develop the character.

    Begin the story now.
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192", # A capable and fast model
            temperature=0.8, # A bit of creativity
            max_tokens=1024,
        )
        script = chat_completion.choices[0].message.content
        print(f"--- Generated Script ---\n{script}\n-----------------------")
        return script
    except Exception as e:
        return f"Error during API call to Groq: {e}"

if __name__ == '__main__':
    # Example of how to run this module directly for testing
    test_topic = "A robot who discovers music for the first time."
    story = generate_story_script(test_topic)
    print(story)
