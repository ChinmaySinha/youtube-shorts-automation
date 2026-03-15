# youtube_agent_system/tools/audio_tools.py
import os
import re
import asyncio
import edge_tts
import time
import whisper_timestamped as whisper
from moviepy.editor import AudioFileClip
from .. import config

def _generate_nvidia_tts(text: str, output_path: str) -> bool:
    """Generate audio using NVIDIA Riva Magpie TTS via gRPC. Returns True on success."""
    try:
        import riva.client
        import riva.client.proto.riva_tts_pb2 as riva_tts
        
        api_key = os.getenv("NVIDIA_API_KEY", "")
        if not api_key:
            print("  NVIDIA API key not found, skipping NVIDIA TTS")
            return False
        
        metadata = [
            ("function-id", config.NVIDIA_TTS_FUNCTION_ID),
            ("authorization", f"Bearer {api_key}")
        ]
        
        auth = riva.client.Auth(
            use_ssl=True,
            uri=config.NVIDIA_TTS_SERVER,
            metadata_args=metadata
        )
        
        tts_service = riva.client.SpeechSynthesisService(auth)
        
        resp = tts_service.synthesize(
            text=text,
            voice_name=config.NVIDIA_TTS_VOICE,
            language_code="en-US",
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hz=44100
        )
        
        # Write WAV file
        import wave
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(44100)
            wav_file.writeframes(resp.audio)
        
        print(f"--- NVIDIA Riva TTS (Leo) wrote audio to {os.path.basename(output_path)} ---")
        return True
        
    except Exception as e:
        print(f"  NVIDIA TTS failed: {e}, falling back to Edge-TTS")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

async def _generate_tts_audio(text: str, voice: str, output_path: str):
    """Async helper function to generate audio using edge-tts with better error handling."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        print(f"--- Edge-TTS successfully wrote audio to {os.path.basename(output_path)} ---")
    except Exception as e:
        print(f"!!! CRITICAL ERROR in Edge-TTS: {e} !!!")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise

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
    """Generates audio for simple sentences (like the title)."""
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:20]
    
    # Try NVIDIA first
    wav_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_title.wav")
    print("--- Generating Title Audio (trying NVIDIA Riva) ---")
    
    if _generate_nvidia_tts(script, wav_path):
        output_path = wav_path
    else:
        # Fallback to Edge-TTS
        print("--- Generating Title Audio with Edge-TTS ---")
        output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_title.mp3")
        try:
            asyncio.run(_generate_tts_audio(script, config.EDGE_TTS_VOICE, output_path))
        except Exception as e:
            print(f"An error occurred during Edge-TTS generation for title: {e}")
            return None

    audio_clip = _wait_for_file_and_load(output_path)
    if not audio_clip:
        return None

    clip_info = [{
        "text": script,
        "audio_path": output_path,
        "duration": audio_clip.duration
    }]
    audio_clip.close()
    return clip_info


def generate_audio_with_word_timestamps(script: str, title: str) -> dict | None:
    """Generate narration audio with word-level timestamps."""
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:20]
    
    wav_output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_full_story.wav")
    mp3_output_path = os.path.join(config.ASSETS_DIR, f"{safe_title}_full_story.mp3")
    audio_for_video = None  # path used for final video

    try:
        # Try NVIDIA Riva first (outputs WAV directly — no conversion needed)
        print("--- Generating Story Audio (trying NVIDIA Riva) ---")
        if _generate_nvidia_tts(script, wav_output_path):
            audio_for_video = wav_output_path
        else:
            # Fallback to Edge-TTS
            print("--- Generating Story Audio with Edge-TTS ---")
            asyncio.run(_generate_tts_audio(script, config.EDGE_TTS_VOICE, mp3_output_path))
            
            print(f"--- Sanitizing audio by converting to WAV format ---")
            mp3_clip = _wait_for_file_and_load(mp3_output_path)
            if not mp3_clip:
                raise IOError("Failed to load generated MP3 for WAV conversion.")
            
            mp3_clip.write_audiofile(wav_output_path, codec='pcm_s16le')
            mp3_clip.close()
            audio_for_video = mp3_output_path
        
        print(f"WAV file ready at: {wav_output_path}")

        # Whisper timestamps on the WAV
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
        return {"audio_path": audio_for_video or wav_output_path, "word_timestamps": word_timestamps}

    except Exception as e:
        print(f"An error occurred during audio generation or timestamping: {e}")
        import traceback
        traceback.print_exc()
        return None