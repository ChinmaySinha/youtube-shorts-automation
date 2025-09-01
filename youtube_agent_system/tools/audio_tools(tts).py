import os
import re
import asyncio
import edge_tts
from moviepy.editor import AudioFileClip
from .. import config

# --- Voice Selection ---
# You can choose any voice from the list available here:
# https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
# A good, popular choice for narrative content is "en-US-JennyNeural".
VOICE = "en-US-JennyNeural"

async def _generate_audio_task(text: str, voice: str, output_path: str):
    """Asynchronous task to generate and save a single audio file."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def text_to_speech_sentences(script: str, topic: str) -> list[dict]:
    """
    Converts a script into a series of sentence-by-sentence audio files
    using the high-quality edge-tts library.
    """
    print("--- Generating Audio for Script (using edge-tts) ---")
    sanitized_topic = re.sub(r'[\s\W]+', '_', topic.lower())
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    audio_clips_info = []

    # The edge-tts library uses asyncio, so we run each task in a new event loop.
    try:
        # Get the current running event loop or create a new one if none exists.
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # If no event loop is running, create a new one.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    for i, sentence in enumerate(sentences):
        if not sentence:
            continue

        output_filename = f"{sanitized_topic}_sentence_{i}.mp3"
        output_path = os.path.join(config.ASSETS_DIR, output_filename)

        try:
            # Run the asynchronous generation task.
            loop.run_until_complete(_generate_audio_task(sentence, VOICE, output_path))

            # Get duration of the saved audio file
            with AudioFileClip(output_path) as audio_clip:
                duration = audio_clip.duration

            audio_clips_info.append({
                "audio_path": output_path,
                "duration": duration,
                "text": sentence
            })
            print(f"Generated audio for sentence {i+1}/{len(sentences)}: {output_path} ({duration:.2f}s)")

        except Exception as e:
            print(f"Error generating audio for sentence: {sentence}. Error: {e}")
            continue

    return audio_clips_info

if __name__ == '__main__':
    test_script = "Hello world. This is a test of the edge-tts library, which provides high-quality, human-like voices for free."
    test_topic = "edge-tts_Test"
    clips = text_to_speech_sentences(test_script, test_topic)
    print("\n--- Results ---")
    print(clips)