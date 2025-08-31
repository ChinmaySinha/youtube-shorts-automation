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

    # This prompt is engineered for creating Reddit-style stories (AITA, ProRevenge, etc.).
    # It instructs the LLM to adopt a first-person, dramatic, and conversational tone.
    prompt = f"""
    You are a skilled writer who specializes in adapting dramatic Reddit titles into compelling, first-person stories.
    Your task is to take the following title and write a full story from the perspective of the person who posted it.

    **Title:** "{topic}"

    **Instructions:**
    1.  **First-Person Narrative:** Write the entire story from the "I" perspective. The narrator is the protagonist.
    2.  **Story Structure:** The story needs a clear beginning that sets the scene (the setup), a middle that details the main conflict, and an end that provides a satisfying resolution or conclusion (the payoff or revenge).
    3.  **Conversational Tone:** Write in a natural, conversational style, as if someone is genuinely sharing their experience online. Use contractions (like "I'm" or "don't"), rhetorical questions, and natural pauses (using ellipses... or em-dashes—) to make the delivery feel more authentic.
    4.  **Word Count:** The story should be between 200 and 300 words, suitable for a short video script.
    5.  **Dramatic and Engaging:** Build suspense and emotion. Make the characters' motivations clear and the conflict compelling.

    **Negative Constraints (What to AVOID):**
    -   Do not write a summary. Write the full story.
    -   Do not be preachy or moralistic. Let the events speak for themselves.
    -   Do not use generic filler phrases like "for some context" or "long story short". Integrate the details naturally.

    Now, write the story based on the title.
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