# Test script to debug Groq response
import sys
sys.path.insert(0, r'c:\Projects\Automated Youtube\Automated_Youtube')

from groq import Groq
from youtube_agent_system import config
import json

print("Testing Groq API...")

client = Groq(api_key=config.GROQ_API_KEY)

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": "Return a simple JSON object: {\"test\": \"hello\", \"number\": 42}"}
        ],
        temperature=0.3,
        max_tokens=100
    )
    
    print("Raw response:")
    raw = response.choices[0].message.content
    print(repr(raw))
    print()
    
    # Try to parse
    json_start = raw.find('{')
    json_end = raw.rfind('}')
    if json_start != -1 and json_end != -1:
        extracted = raw[json_start:json_end + 1]
        print("Extracted JSON:", extracted)
        parsed = json.loads(extracted)
        print("Parsed successfully:", parsed)
    else:
        print("No JSON braces found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
