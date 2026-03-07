# Check Edge-TTS available voices
import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    print("Available en-US voices:")
    for v in voices:
        if 'en-US' in v['Name'] and 'Neural' in v['Name']:
            print(f"  {v['Name']}")

asyncio.run(main())
