import random
from . import config
from .tools import rival_scanner

# A simple in-memory set to keep track of topics we've already produced.
# In a real system, this would be stored in a persistent database (like the knowledge_base).
__processed_topics = set()

def _get_new_rival_topics() -> list[str]:
    """Scans rival URLs and returns any new, unprocessed video titles."""
    print("--- Strategy Agent: Scanning rival channels for new topics ---")
    new_topics = []
    for url in config.RIVAL_VIDEO_URLS:
        title = rival_scanner.get_video_title(url)
        # Check if we got a title and if we haven't processed it before
        if title and title not in __processed_topics:
            new_topics.append(title)

    if not new_topics:
        print("No new topics found from rival channels.")

    return new_topics

def decide_content_topic() -> str:
    """
    Decides on the next video topic, making the pipeline autonomous.

    The logic is:
    1. Try to get a new topic from a rival channel.
    2. If none, fall back to the static pool of Reddit ideas.
    3. If the static pool is exhausted, use the final fallback topic.

    Returns:
        A string topic for the next video.
    """
    print("--- 🤔 Strategy Agent: Deciding next topic... ---")

    # Priority 1: Get a new topic from a rival channel
    rival_topics = _get_new_rival_topics()
    if rival_topics:
        # Just pick the first new one we find
        next_topic = rival_topics[0]
        print(f"New rival topic selected: '{next_topic}'")
        __processed_topics.add(next_topic)
        return next_topic

    # Priority 2: Get an unused topic from our static pool
    print("Falling back to static topic pool.")
    available_topics = [t for t in config.STATIC_TOPIC_POOL if t not in __processed_topics]

    if available_topics:
        next_topic = random.choice(available_topics)
        print(f"Static topic selected: '{next_topic}'")
        __processed_topics.add(next_topic)
        return next_topic

    # Priority 3: Final fallback if all topics have been used
    print("All topic pools exhausted. Using default fallback topic.")
    return config.DEFAULT_TOPIC

if __name__ == '__main__':
    # Example of how the agent decides on a topic
    next_topic = decide_content_topic()
    print(f"\n--- Decision ---")
    print(f"The next video topic will be: {next_topic}")

    # Show what happens when it runs again (the first topic is now "processed")
    print("\n--- Running agent again ---")
    next_topic_2 = decide_content_topic()
    print(f"\n--- Decision 2 ---")
    print(f"The next video topic will be: {next_topic_2}")
