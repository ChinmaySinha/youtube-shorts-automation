import random
from groq import Groq
from . import config
from .tools import rival_scanner
from . import knowledge_base

# A simple in-memory set to keep track of topics we've already produced.
# In a real system, this would be stored in a persistent database.
__processed_topics = set()

def _get_new_rival_topics() -> list[str]:
    """Scans rival URLs and returns any new, unprocessed video titles."""
    print("--- Strategy Agent: Scanning rival channels for new topics ---")
    new_topics = []
    for url in config.RIVAL_VIDEO_URLS:
        title = rival_scanner.get_video_title(url)
        if title and title not in __processed_topics:
            new_topics.append(title)
    if not new_topics:
        print("No new topics found from rival channels.")
    return new_topics

def _generate_new_topics_from_insights() -> list[str]:
    """
    Uses an LLM to generate new topic ideas based on past performance.
    """
    print("--- Strategy Agent: Generating new topics from past performance ---")
    all_insights = knowledge_base.get_all_insights()

    if not all_insights:
        print("No past insights found in the knowledge base. Cannot generate new topics.")
        return []

    client = Groq(api_key=config.GROQ_API_KEY)

    # We combine all insights into a single context block for the LLM
    insights_context = "\n".join(all_insights)

    prompt = f"""
    You are a brilliant YouTube content strategist. Your goal is to come up with new, viral video ideas.
    You will be given a summary of the performance of past videos. Based on this data, you need to generate a list of 5 new, original Reddit-style video titles that are likely to perform well.

    **Past Performance Data:**
    {insights_context}

    **Your Task:**
    Analyze the performance data above. Identify what makes a video successful (e.g., topics about revenge, family drama, workplace conflicts).
    Generate a list of 5 new, clickable, and dramatic video titles in the style of "AITA for..." or "My entitled...".
    The titles should be creative and original, not just copies of past successes.

    **Output Format:**
    Return the list as a numbered list, with each title on a new line. For example:
    1. AITA for telling my sister her destination wedding was a tacky gift grab?
    2. My landlord tried to evict me illegally, so I used his own rules to bankrupt him.
    3. ...
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.9, # Higher temperature for more creative ideas
        )
        response_text = chat_completion.choices[0].message.content

        # Parse the numbered list response from the LLM
        new_topics = [line.split('. ', 1)[1] for line in response_text.strip().split('\n') if '. ' in line]
        print(f"Generated {len(new_topics)} new data-driven topics.")
        return new_topics
    except Exception as e:
        print(f"Error generating new topics from LLM: {e}")
        return []


def decide_content_topic() -> str:
    """
    Decides on the next video topic using a learning, multi-tiered strategy.
    """
    print("--- 🤔 Strategy Agent (v2): Deciding next topic... ---")

    # Priority 1: Generate new topics from past performance
    generated_topics = _generate_new_topics_from_insights()
    # Filter out any we might have already processed
    available_generated_topics = [t for t in generated_topics if t not in __processed_topics]
    if available_generated_topics:
        next_topic = random.choice(available_generated_topics)
        print(f"Data-driven topic selected: '{next_topic}'")
        __processed_topics.add(next_topic)
        return next_topic

    # Priority 2: Get a new topic from a rival channel
    rival_topics = _get_new_rival_topics()
    if rival_topics:
        next_topic = rival_topics[0]
        print(f"New rival topic selected: '{next_topic}'")
        __processed_topics.add(next_topic)
        return next_topic

    # Priority 3: Get an unused topic from our static pool
    print("Falling back to static topic pool.")
    available_static_topics = [t for t in config.STATIC_TOPIC_POOL if t not in __processed_topics]
    if available_static_topics:
        next_topic = random.choice(available_static_topics)
        print(f"Static topic selected: '{next_topic}'")
        __processed_topics.add(next_topic)
        return next_topic

    # Priority 4: Final fallback
    print("All topic pools exhausted. Using default fallback topic.")
    return config.DEFAULT_TOPIC

if __name__ == '__main__':
    # This test requires some pre-existing data in the knowledge base
    print("--- Testing Strategy Agent v2 ---")
    # Let's add a dummy insight to simulate a past success
    knowledge_base.save_insight(
        "dummy_id_1",
        "Video 'Pro revenge on my boss' was highly successful with 100k views.",
        {"topic": "Pro revenge on my boss", "views": 100000}
    )

    next_topic = decide_content_topic()
    print(f"\n--- Decision ---")
    print(f"The next video topic will be: {next_topic}")
