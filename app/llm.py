from __future__ import annotations

from .config import GEMINI_API_KEY, GEMINI_MODEL, LLAMA_BASE_URL, LLAMA_MODEL

def call_llama(system_prompt: str, user_prompt: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(base_url=LLAMA_BASE_URL, api_key="ollama")
        response = client.chat.completions.create(model=LLAMA_MODEL, messages=[
            {"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}
        ], temperature=0)
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise RuntimeError(f"Llama is unavailable at {LLAMA_BASE_URL}: {exc}") from exc

def call_gemini(system_prompt: str, user_prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini is unavailable: set GEMINI_API_KEY in .env.")
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=f"{system_prompt}\n\n{user_prompt}")
        return response.text or ""
    except Exception as exc:
        raise RuntimeError(f"Gemini is unavailable: {exc}") from exc

def health() -> dict[str, str]:
    result = {"Mock": "available", "Llama": "unavailable", "Gemini": "available" if GEMINI_API_KEY else "unavailable"}
    try:
        import urllib.request
        urllib.request.urlopen(LLAMA_BASE_URL.rsplit("/v1", 1)[0] + "/api/tags", timeout=1)
        result["Llama"] = "available"
    except Exception:
        pass
    return result
