"""
Standalone demo of the multi-tier LLM extraction engine (Phase III).

Run this after setting at least one of GEMINI_API_KEY / GROQ_API_KEY /
DEEPSEEK_API_KEY in a .env file (see .env.example). It feeds a couple of
sample descriptions through the fallback chain and prints what each tier
returned - useful as evidence in your submission that the chain actually
works, not just described in a doc.

Without any keys set, every tier will fail and log a clear warning - that's
expected and shows the fallback logic itself is working correctly.
"""

import asyncio

import aiohttp

import config
from llm_orchestrator import extract_structured, parse_llm_json
from logging_setup import get_logger

logger = get_logger("demo_llm")

SAMPLE_TEXTS = [
    "Anthropic is an AI safety company based in San Francisco with roughly 500 "
    "employees, offering both free and paid tiers of its Claude assistant.",
    "OpenAI, Inc. builds general-purpose AI systems and offers ChatGPT under a "
    "freemium pricing model, with over 1000 employees globally.",
]


async def main():
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_LLM_CALLS)
    async with aiohttp.ClientSession() as session:
        for text in SAMPLE_TEXTS:
            logger.info(f"Input: {text[:70]}...")
            raw_results = await extract_structured(session, text, semaphore)
            if raw_results:
                for raw in raw_results:
                    parsed = parse_llm_json(raw)
                    logger.info(f"Extracted: {parsed}")
            else:
                logger.error("All tiers failed for this input - check your API keys in .env")


if __name__ == "__main__":
    asyncio.run(main())
