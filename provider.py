"""
Thin wrappers around Gemini (Google AI Studio), Groq, and DeepSeek (via OpenRouter).
Requires: pip install google-genai groq requests
"""

import requests
from google import genai
from groq import Groq

from config import (
    GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY,
    GEMINI_MODEL, GROQ_MODEL, CRITIC_MODEL,
)

# Clients are created lazily (on first use) so a missing key gives a clear
# error message from the function that needs it, instead of crashing on
# import before you even get to run anything.
_gemini_client = None
_groq_client = None

# Disabling AFC (Automatic Function Calling) in generate_content config.
# We never pass tools, so AFC is irrelevant — disabling it prevents the SDK
# from emitting its "direct AFC not recommended" warning.
_NO_AFC = genai.types.GenerateContentConfig(
    automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
        disable=True,
    )
)


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is missing — check your .env file.")
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is missing — check your .env file.")
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def ask_gemini(prompt: str, system: str = "") -> str:
    """
    Long-context synthesis / summarization. Best for combining lots of
    search results into one coherent answer.
    """
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        client = _get_gemini_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=_NO_AFC,
        )
        return response.text.strip()
    except Exception as e:
        return f"[Gemini error] {e}"



def ask_groq(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """
    Fast, cheap reasoning. Best for planning, routing, and quick checks.
    """
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Groq error] {e}"


def ask_critic(prompt: str, system: str = "You are a rigorous, logical reviewer.") -> str:
    """
    Strong step-by-step reasoning. Best for critique / consistency checking,
    where catching contradictions and gaps matters more than speed.

    Calls OpenRouter directly via requests (not the openai SDK) to avoid
    SDK-version incompatibilities with custom base_url setups. Uses
    "openrouter/free" which auto-picks from currently available free
    models — more resilient than pinning one model that might get pulled.
    """
    if not OPENROUTER_API_KEY:
        return "[Critic error] OPENROUTER_API_KEY is missing — check your .env file."
    try:
        resp = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": CRITIC_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Critic error] {e}"