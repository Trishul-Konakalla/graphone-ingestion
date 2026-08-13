import asyncio
import json
import re

import aiohttp

import config
from logging_setup import get_logger

logger = get_logger("llm")


class RateLimitError(Exception):
    """Raised on HTTP 429 from any provider."""


class PayloadTooLargeError(Exception):
    """Raised on HTTP 413 from any provider."""


def chunk_text(text: str, max_chars: int = config.MAX_CHARS_PER_CHUNK) -> list[str]:
    """Splits text into chunks under max_chars, breaking on paragraph boundaries
    where possible so payloads never trigger 413s while staying semantically dense."""
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= max_chars:
            current += p + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            if len(p) > max_chars:
                for i in range(0, len(p), max_chars):
                    chunks.append(p[i:i + max_chars])
                current = ""
            else:
                current = p + "\n\n"
    if current:
        chunks.append(current.strip())
    return chunks


EXTRACTION_PROMPT = """Extract the following fields from the text below as strict JSON only \
(no markdown fences, no commentary):
{{"entityName": "", "employeeCount": null, "pricingModel": "", "summary": ""}}

TEXT:
{text}
"""


async def _call_gemini(session: aiohttp.ClientSession, prompt: str) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    url = config.GEMINI_URL.format(key=config.GEMINI_API_KEY)
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    async with session.post(url, json=payload, timeout=30) as resp:
        if resp.status == 429:
            raise RateLimitError("Gemini rate limited")
        if resp.status == 413:
            raise PayloadTooLargeError("Gemini payload too large")
        resp.raise_for_status()
        data = await resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def _call_groq(session: aiohttp.ClientSession, prompt: str) -> str:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
    payload = {"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}]}
    async with session.post(config.GROQ_URL, json=payload, headers=headers, timeout=30) as resp:
        if resp.status == 429:
            raise RateLimitError("Groq rate limited")
        if resp.status == 413:
            raise PayloadTooLargeError("Groq payload too large")
        resp.raise_for_status()
        data = await resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_deepseek(session: aiohttp.ClientSession, prompt: str) -> str:
    if not config.DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    headers = {"Authorization": f"Bearer {config.DEEPSEEK_API_KEY}"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
    async with session.post(config.DEEPSEEK_URL, json=payload, headers=headers, timeout=30) as resp:
        if resp.status == 429:
            raise RateLimitError("DeepSeek rate limited")
        if resp.status == 413:
            raise PayloadTooLargeError("DeepSeek payload too large")
        resp.raise_for_status()
        data = await resp.json()
        return data["choices"][0]["message"]["content"]


def parse_llm_json(raw: str) -> dict | None:
    """Strips markdown fences if present and parses the model's JSON output."""
    if not raw:
        return None
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse LLM output as JSON: {cleaned[:120]}...")
        return None


TIER_CHAIN = [
    ("gemini-1.5-flash", _call_gemini),
    ("groq-llama3-70b", _call_groq),
    ("deepseek-chat", _call_deepseek),
]


async def extract_structured(
    session: aiohttp.ClientSession, raw_text: str, semaphore: asyncio.Semaphore
) -> list[str] | None:
    """Runs the multi-tier fallback chain (Gemini Flash -> Groq Llama 3 -> DeepSeek)
    on each chunk of raw_text. On a 429, backs off and retries the SAME tier before
    falling back. On a 413 or any other failure, falls straight to the next tier.
    Returns a list of raw model responses (one per chunk), or None if every tier failed
    for every chunk.
    """
    chunks = chunk_text(raw_text)
    results = []

    for chunk in chunks:
        prompt = EXTRACTION_PROMPT.format(text=chunk)
        chunk_result = None

        for tier_name, call_fn in TIER_CHAIN:
            async with semaphore:
                for attempt in range(1, config.MAX_RETRIES + 1):
                    try:
                        chunk_result = await call_fn(session, prompt)
                        logger.info(f"Extraction succeeded via {tier_name}")
                        break
                    except RateLimitError:
                        wait = config.BASE_BACKOFF_SECONDS ** attempt + (0.1 * attempt)
                        logger.warning(
                            f"{tier_name} 429 rate limited, backing off {wait:.1f}s "
                            f"(attempt {attempt}/{config.MAX_RETRIES})"
                        )
                        await asyncio.sleep(wait)
                        continue
                    except PayloadTooLargeError:
                        logger.warning(f"{tier_name} 413 even after chunking - falling back")
                        break
                    except Exception as e:
                        logger.warning(f"{tier_name} failed: {e}. Falling back to next tier.")
                        break
            if chunk_result:
                break

        if chunk_result:
            results.append(chunk_result)
        else:
            logger.error("All LLM tiers failed for this chunk")

    return results if results else None
