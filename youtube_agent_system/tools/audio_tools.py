import os
import re
from gtts import gTTS
from moviepy.editor import AudioFileClip  # Corrected import path
from .. import config

def text_to_speech_sentences(script: str, topic: str) -> list[dict]:
    """
    Converts a script into a series of sentence-by-sentence audio files.
    """
    print("--- Generating Audio for Script ---")
    sanitized_topic = re.sub(r'[\s\W]+', '_', topic.lower())
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    audio_clips_info = []

    for i, sentence in enumerate(sentences):
        if not sentence:
            continue

        output_filename = f"{sanitized_topic}_sentence_{i}.mp3"
        output_path = os.path.join(config.ASSETS_DIR, output_filename)

        try:
            tts = gTTS(
                text=sentence,
                lang=config.VOICEOVER_LANGUAGE,
                tld=config.VOICEOVER_Tld,
                slow=False
            )
            tts.save(output_path)

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
    test_script = "Hello world. This is a test of the text to speech system. Isn't it wonderful?"
    test_topic = "gTTS Test"
    clips = text_to_speech_sentences(test_script, test_topic)
    print("\n--- Results ---")
    print(clips)
