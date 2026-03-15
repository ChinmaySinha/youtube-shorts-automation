# youtube_agent_system/tools/llm_client.py
"""
Shared LLM client that uses NVIDIA Nemotron Ultra 253B as primary,
falling back to Groq if NVIDIA is unavailable.
"""
import os
import requests
from .. import config

# NVIDIA NIM cloud API (OpenAI-compatible)
NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

# Optimal params for viral YouTube Shorts content:
#   - temperature 0.8: creative enough for hooks, still coherent
#   - top_p 0.9: good diversity
#   - frequency_penalty 0.3: reduces repetitive phrasing
#   - presence_penalty 0.15: encourages new topics/vocab
DEFAULT_PARAMS = {
    "temperature": 0.8,
    "top_p": 0.9,
    "frequency_penalty": 0.3,
    "presence_penalty": 0.15,
    "max_tokens": 4096,
}

# For adaptation (stay more faithful to source material)
ADAPTATION_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "frequency_penalty": 0.2,
    "presence_penalty": 0.1,
    "max_tokens": 4096,
}

# For SEO metadata (structured, precise output)
SEO_PARAMS = {
    "temperature": 0.75,
    "top_p": 0.9,
    "frequency_penalty": 0.2,
    "presence_penalty": 0.1,
    "max_tokens": 1024,
}


def chat_completion(messages: list[dict], params: dict = None, task: str = "general") -> str | None:
    """
    Call LLM with NVIDIA Nemotron first, fall back to Groq.
    
    Args:
        messages: OpenAI-format messages [{"role": "user", "content": "..."}]
        params: Override default params. Use ADAPTATION_PARAMS or SEO_PARAMS for specific tasks.
        task: Label for logging (e.g. "script_generation", "seo_metadata")
    
    Returns:
        Response text string, or None on failure.
    """
    p = params or DEFAULT_PARAMS
    
    # Try NVIDIA Nemotron first
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    if nvidia_key:
        try:
            print(f"  [LLM] Using NVIDIA Nemotron Ultra 253B for {task}")
            resp = requests.post(
                f"{NVIDIA_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": NVIDIA_MODEL,
                    "messages": messages,
                    **p,
                },
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"].strip()
            print(f"  [LLM] NVIDIA response received ({len(result)} chars)")
            return result
        except Exception as e:
            print(f"  [LLM] NVIDIA failed: {e}, falling back to Groq")
    
    # Fallback to Groq
    if config.GROQ_API_KEY:
        try:
            from groq import Groq
            print(f"  [LLM] Falling back to Groq for {task}")
            client = Groq(api_key=config.GROQ_API_KEY)
            chat = client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                temperature=p.get("temperature", 0.7),
                top_p=p.get("top_p", 0.95),
                max_tokens=p.get("max_tokens", 4096),
            )
            result = chat.choices[0].message.content.strip()
            print(f"  [LLM] Groq response received ({len(result)} chars)")
            return result
        except Exception as e:
            print(f"  [LLM] Groq also failed: {e}")
    
    print(f"  [LLM] All LLM providers failed for {task}")
    return None
