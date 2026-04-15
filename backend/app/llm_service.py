from __future__ import annotations

import json
import re
from typing import Any

import requests

from app.config import settings


class LLMUnavailableError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


def llm_available() -> bool:
    provider = settings.llm_provider
    if not provider:
        return False
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "groq":
        return bool(settings.groq_api_key)
    if provider == "ollama":
        return bool(settings.ollama_base_url)
    return False


def _extract_json_block(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise LLMResponseError(f"Model response did not contain valid JSON. Raw response: {text[:1000]}")
        return json.loads(match.group(0))


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("openai package is not installed.") from exc

    if not settings.openai_api_key:
        raise LLMUnavailableError("OPENAI_API_KEY is missing.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=3000,
    )
    return response.choices[0].message.content or ""


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    try:
        from groq import Groq
    except ImportError as exc:
        raise LLMUnavailableError("groq package is not installed.") from exc

    if not settings.groq_api_key:
        raise LLMUnavailableError("GROQ_API_KEY is missing.")

    print("[llm_service] Calling Groq...")
    print(f"[llm_service] Provider: {settings.llm_provider}")
    print(f"[llm_service] Model: {settings.groq_model}")
    print(f"[llm_service] Key present: {bool(settings.groq_api_key)}")

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=3000,
    )
    content = response.choices[0].message.content or ""
    print("[llm_service] Groq response received.")
    return content


def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "")


def call_json(system_prompt: str, user_prompt: str) -> Any:
    if not llm_available() or not settings.enable_llm_recommender:
        raise LLMUnavailableError(
            f"LLM provider is not configured. "
            f"Provider='{settings.llm_provider}', "
            f"enabled={settings.enable_llm_recommender}, "
            f"groq_key_present={bool(settings.groq_api_key)}"
        )

    provider = settings.llm_provider
    print(f"[llm_service] call_json invoked with provider='{provider}'")

    if provider == "openai":
        raw = _call_openai(system_prompt, user_prompt)
    elif provider == "groq":
        raw = _call_groq(system_prompt, user_prompt)
    elif provider == "ollama":
        raw = _call_ollama(system_prompt, user_prompt)
    else:
        raise LLMUnavailableError(f"Unsupported LLM provider: {provider}")

    return _extract_json_block(raw)