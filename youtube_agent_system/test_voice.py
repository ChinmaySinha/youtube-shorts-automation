# Test Edge-TTS with DavisMultilingualNeural
import asyncio
import edge_tts
import os

voice = "en-US-DavisMultilingualNeural"
test_text = "Hello! This is a test of the Davis Multilingual Neural voice. Testing one, two, three."
output_path = "test_audio.mp3"

async def test_tts():
    print(f"Testing voice: {voice}")
    communicate = edge_tts.Communicate(test_text, voice)
    await communicate.save(output_path)
    print(f"Audio saved to {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

try:
    asyncio.run(test_tts())
    print("SUCCESS! Voice works.")
except Exception as e:
    print(f"FAILED: {e}")
