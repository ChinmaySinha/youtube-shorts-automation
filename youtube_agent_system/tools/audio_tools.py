import os
import re
from gtts import gTTS
from moviepy import AudioFileClip
from .. import config

def text_to_speech_sentences(script: str, topic: str) -> list[dict]:
    """
    Converts a script into a series of sentence-by-sentence audio files.

    Args:
        script: The text script to convert.
        topic: The topic of the video, used for naming files.

    Returns:
        A list of dictionaries, where each dictionary contains:
        'audio_path': The path to the generated audio file for a sentence.
        'duration': The duration of the audio clip in seconds.
        'text': The sentence text.
    """
    print("--- Generating Audio for Script ---")
    # Clean and simple topic name for filenames
    sanitized_topic = re.sub(r'[\s\W]+', '_', topic.lower())

    # Split script into sentences. A simple regex to handle ., !, ?
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())

    audio_clips_info = []

    for i, sentence in enumerate(sentences):
        if not sentence:
            continue

        output_filename = f"{sanitized_topic}_sentence_{i}.mp3"
        output_path = os.path.join(config.ASSETS_DIR, output_filename)

        try:
            # Create gTTS object
            tts = gTTS(
                text=sentence,
                lang=config.VOICEOVER_LANGUAGE,
                tld=config.VOICEOVER_Tld,
                slow=False
            )
            tts.save(output_path)

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
    # Example usage
    test_script = "Hello world. This is a test of the text to speech system. Isn't it wonderful?"
    test_topic = "gTTS Test"
    clips = text_to_speech_sentences(test_script, test_topic)
    print("\n--- Results ---")
    print(clips)
