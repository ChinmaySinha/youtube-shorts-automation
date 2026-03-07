import os
from groq import Groq
from . import config
from . import knowledge_base


def generate_story_script(topic: str) -> str:
    """
    Generates a compelling, human-like story script using an LLM.

    Uses retrieval-augmented few-shot prompting: pulls similar high-quality 
    stories from the training database and includes them as reference examples
    in the prompt. This produces dramatically better output than a bare prompt.

    Args:
        topic: The central theme or topic for the story.

    Returns:
        A string containing the generated story script.
        Returns an error message if the API key is not configured.
    """
    if not config.GROQ_API_KEY:
        return "Error: GROQ_API_KEY is not configured in the .env file."

    client = Groq(api_key=config.GROQ_API_KEY)

    # --- Retrieve similar training stories as few-shot examples ---
    example_stories = knowledge_base.get_similar_training_stories(
        query=topic,
        n_results=3
    )

    # Build the examples section
    examples_section = ""
    if example_stories:
        examples_section = "\n\n**REFERENCE EXAMPLES (Real viral stories — match this quality and tone):**\n"
        for i, story in enumerate(example_stories, 1):
            # Truncate to keep prompt manageable
            body_preview = story['body'][:600] if len(story['body']) > 600 else story['body']
            examples_section += f"""
--- EXAMPLE {i} ---
Title: {story['title']}
Category: {story['category']}
Story:
{body_preview}
--- END EXAMPLE {i} ---
"""
        examples_section += """
**IMPORTANT:** The examples above show the QUALITY, TONE, and STYLE we want. 
Do NOT copy these stories. Write an ORIGINAL story inspired by the title below.
Your story should feel just as authentic, dramatic, and emotionally engaging as these examples.
"""
        training_count = knowledge_base.get_training_story_count()
        print(f"--- [ContentAgent] Using {len(example_stories)} reference examples (from {training_count} total training stories) ---")
    else:
        print("--- [ContentAgent] No training stories available — using enhanced prompt only ---")

    # --- Build the prompt ---
    prompt = f"""You are a skilled writer who specializes in adapting dramatic Reddit titles into compelling, first-person stories.
Your task is to take the following title and write a full story from the perspective of the person who posted it.
{examples_section}
**Title:** "{topic}"

**Instructions:**
1.  **First-Person Narrative:** Write the entire story from the "I" perspective. The narrator is the protagonist.
2.  **Story Structure:** The story needs a clear beginning that sets the scene (the setup), a middle that details the main conflict, and an end that provides a satisfying resolution or conclusion (the payoff or revenge).
3.  **Conversational Tone:** Write in a natural, conversational style, as if someone is genuinely sharing their experience online. Use contractions (like "I'm" or "don't"), rhetorical questions, and natural pauses (using ellipses... or em-dashes—) to make the delivery feel more authentic.
4.  **Hook the Reader Instantly:** The FIRST sentence must be shocking, intriguing, or emotionally gripping. No slow intros. Start with a punch.
5.  **Emotional Depth:** Show real emotions — frustration, disbelief, satisfaction, hurt. The reader should FEEL what the narrator feels.
6.  **Specific Details:** Include realistic, specific details (names, places, amounts, times) that make the story feel genuine. Don't be vague.
7.  **Word Count:** The story should be between 200 and 300 words, suitable for a short video script.
8.  **Dramatic and Engaging:** Build suspense and emotion. Make the characters' motivations clear and the conflict compelling.

**Negative Constraints (What to AVOID):**
-   Do not write a summary. Write the full story.
-   Do not be preachy or moralistic. Let the events speak for themselves.
-   Do not use generic filler phrases like "for some context" or "long story short". Integrate the details naturally.
-   Do not start with "So..." or "Well..." — start with something that GRABS attention.
-   Do not use any hashtags, emojis, or social media formatting.

Now, write the story based on the title."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=1024,
        )
        script = chat_completion.choices[0].message.content
        print(f"--- Generated Script ---\n{script}\n-----------------------")
        return script
    except Exception as e:
        return f"Error during API call to Groq: {e}"


if __name__ == '__main__':
    # Test generation with and without training data
    print("=" * 60)
    print("CONTENT AGENT — Story Generation Test")
    print("=" * 60)
    
    # Check training data status
    count = knowledge_base.get_training_story_count()
    print(f"\nTraining stories loaded: {count}")
    
    if count > 0:
        print("[OK] Using RAG-powered few-shot prompting")
    else:
        print("[WARN] No training data -- run train_story_model.py first for best results")
    
    test_topic = "AITA for refusing to give up my first-class seat for a celebrity's child?"
    print(f"\nGenerating story for: {test_topic}\n")
    story = generate_story_script(test_topic)
    print(story)