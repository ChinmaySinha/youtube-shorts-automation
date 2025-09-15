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
    """Async helper function to generate audio using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def text_to_speech_sentences(script: str, title: str) -> list[dict] | None:
    """
    Generates audio for simple sentences (like the title) using Edge-TTS.
    """
    print("--- 🔊 Generating Title Audio with Edge-TTS ---")
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:20]
    output_filename = f"{safe_title}_title.mp3"
    output_path = os.path.join(config.ASSETS_DIR, output_filename)

    try:
        asyncio.run(_generate_tts_audio(script, config.EDGE_TTS_VOICE, output_path))
        time.sleep(1.0) 

        audio_clip = AudioFileClip(output_path)
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
    """
    (REWRITTEN FOR STABILITY)
    Generates an MP3, converts it to a stable WAV file, then uses Whisper for timestamps.
    """
    print("--- 🔊 Generating Audio with Edge-TTS ---")
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:20]
    
    # Define paths for both MP3 and the new WAV file
    mp3_output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_full_story.mp3")
    wav_output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_full_story.wav")

    try:
        # Step 1: Generate the initial MP3 audio file
        asyncio.run(_generate_tts_audio(script, config.EDGE_TTS_VOICE, mp3_output_path))
        print(f"Audio file generated with Edge-TTS at: {mp3_output_path}")
        time.sleep(1.0)

        # Step 2: Convert the MP3 to a stable WAV file to ensure compatibility
        print(f"---  sanitizing audio by converting to WAV format ---")
        with AudioFileClip(mp3_output_path) as audio_clip:
            audio_clip.write_audiofile(wav_output_path, codec='pcm_s16le')
        print(f"Sanitized WAV file saved at: {wav_output_path}")

        # Step 3: Use Whisper on the clean WAV file to get precise timestamps
        print("--- 🎤 Analyzing audio for precise word timestamps with Whisper ---")
        audio = whisper.load_audio(wav_output_path)
        model = whisper.load_model("tiny", device="cpu") 
        result = whisper.transcribe(model, audio, language="en")

        word_timestamps = []
        for segment in result["segments"]:
            for word_info in segment["words"]:
                word = word_info["text"].strip()
                start = word_info["start"]
                end = word_info["end"]
                duration = end - start
                
                word_timestamps.append({
                    "word": word,
                    "start": start,
                    "duration": duration
                })
        
        if not word_timestamps:
            raise ValueError("Whisper could not detect any words in the audio.")

        print(f"Generated precise timestamps for {len(word_timestamps)} words.")
        # Return the original MP3 path for the final video, but the WAV was used for analysis
        return {"audio_path": mp3_output_path, "word_timestamps": word_timestamps}

    except Exception as e:
        print(f"An error occurred during audio generation or timestamping: {e}")
        import traceback
        traceback.print_exc()
        return None