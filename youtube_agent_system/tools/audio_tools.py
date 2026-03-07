# youtube_agent_system/tools/audio_tools.py
import os
import re
import asyncio
import edge_tts
import time
import whisper_timestamped as whisper
from moviepy.editor import AudioFileClip
from .. import config

async def _generate_tts_audio(text: str, voice: str, output_path: str):
    """Async helper function to generate audio using edge-tts with better error handling."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        print(f"--- Edge-TTS successfully wrote audio to {os.path.basename(output_path)} ---")
    except Exception as e:
        # This will now catch any error during the TTS generation and save process.
        print(f"!!! CRITICAL ERROR in Edge-TTS: {e} !!!")
        # Ensure a failed generation doesn't leave behind an empty/corrupt file.
        if os.path.exists(output_path):
            os.remove(output_path)
        raise  # Re-raise the exception so the main function knows it failed.

def _wait_for_file_and_load(path: str, timeout: int = 60) -> AudioFileClip | None:
    """Waits patiently for a file to be fully written and stable before loading it."""
    start_time = time.time()
    last_size = -1
    stable_time = None

    print(f"--- Waiting for audio file to be ready: {os.path.basename(path)} ---")

    while time.time() - start_time < timeout:
        if os.path.exists(path):
            current_size = os.path.getsize(path)
            if current_size > 0 and current_size == last_size:
                if stable_time is None:
                    stable_time = time.time()
                elif time.time() - stable_time >= 1.0:
                    print("File size is stable. Attempting to load.")
                    try:
                        clip = AudioFileClip(path)
                        print("Successfully loaded audio file.")
                        return clip
                    except Exception as e:
                        print(f"Error loading stable file: {e}. Aborting.")
                        return None
            else:
                stable_time = None
                last_size = current_size
        
        time.sleep(0.5)

    print(f"Error: Timed out after {timeout} seconds waiting for file: {os.path.basename(path)}")
    return None


def text_to_speech_sentences(script: str, title: str) -> list[dict] | None:
    """Generates audio for simple sentences (like the title) using Edge-TTS."""
    print("--- Generating Title Audio with Edge-TTS ---")
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:20]
    output_filename = f"{safe_title}_title.mp3"
    output_path = os.path.join(config.ASSETS_DIR, output_filename)

    try:
        asyncio.run(_generate_tts_audio(script, config.EDGE_TTS_VOICE, output_path))
        
        audio_clip = _wait_for_file_and_load(output_path)
        if not audio_clip:
            raise IOError("Failed to load generated title audio.")

        clip_info = [{
            "text": script,
            "audio_path": output_path,
            "duration": audio_clip.duration
        }]
        audio_clip.close()
        return clip_info
        
    except Exception as e:
        print(f"An error occurred during Edge-TTS generation for title: {e}")
        return None

def generate_audio_with_word_timestamps(script: str, title: str) -> dict | None:
    """(REWRITTEN FOR MAXIMUM STABILITY)"""
    print("--- Generating Audio with Edge-TTS ---")
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:20]
    
    mp3_output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_full_story.mp3")
    wav_output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_full_story.wav")

    try:
        # Step 1: Generate the initial MP3 audio file. The new error handling inside
        # _generate_tts_audio will catch any failures here.
        asyncio.run(_generate_tts_audio(script, config.EDGE_TTS_VOICE, mp3_output_path))
        
        # Step 2: Use the robust helper to wait for the MP3 and load it
        print(f"--- Sanitizing audio by converting to WAV format ---")
        mp3_clip = _wait_for_file_and_load(mp3_output_path)
        if not mp3_clip:
            raise IOError("Failed to load generated MP3 for WAV conversion.")
        
        mp3_clip.write_audiofile(wav_output_path, codec='pcm_s16le')
        mp3_clip.close()
        print(f"Sanitized WAV file saved at: {wav_output_path}")

        # Step 3: Use Whisper on the clean WAV file
        print("--- Analyzing audio for precise word timestamps with Whisper ---")
        audio = whisper.load_audio(wav_output_path)
        model = whisper.load_model("tiny", device="cpu") 
        result = whisper.transcribe(model, audio, language="en")

        word_timestamps = []
        for segment in result["segments"]:
            for word_info in segment["words"]:
                word_timestamps.append({
                    "word": word_info["text"].strip(),
                    "start": word_info["start"],
                    "duration": word_info["end"] - word_info["start"]
                })
        
        if not word_timestamps:
            raise ValueError("Whisper could not detect any words in the audio.")

        print(f"Generated precise timestamps for {len(word_timestamps)} words.")
        return {"audio_path": mp3_output_path, "word_timestamps": word_timestamps}

    except Exception as e:
        print(f"An error occurred during audio generation or timestamping: {e}")
        import traceback
        traceback.print_exc()
        return None