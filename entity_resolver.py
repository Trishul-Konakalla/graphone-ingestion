import re

import pandas as pd
from rapidfuzz import fuzz, process

from logging_setup import get_logger

logger = get_logger("entity_resolver")

# Mock seed database of ~50 known AI startups (Phase IV requirement).
CANONICAL_SEED = [
    "OpenAI", "Anthropic", "Google DeepMind", "Mistral AI", "Perplexity",
    "Cohere", "Stability AI", "Hugging Face", "Scale AI", "Databricks",
    "xAI", "Inflection AI", "Adept AI", "Character.AI", "Runway",
    "ElevenLabs", "Together AI", "Groq", "Cerebras", "SambaNova",
    "Replit", "Vercel", "LangChain", "Pinecone", "Weaviate",
    "Glean", "Harvey", "Sierra", "Cursor", "Codeium",
    "Synthesia", "Descript", "Jasper", "Writer", "Typeface",
    "Adobe Firefly", "Midjourney", "Ideogram", "Luma AI", "Pika",
    "Suno", "Udio", "Weights & Biases", "Fireworks AI", "Baseten",
    "Modal", "Replicate", "Voyage AI", "Contextual AI", "Reka AI",
]

SUFFIX_PATTERN = re.compile(
    r"[,.]?\s*\b(inc|inc\.|ltd|ltd\.|llc|pbc|corp|corporation|co|company|"
    r"technologies|technology|labs?|\.ai|\.io)\b\.?",
    re.IGNORECASE,
)


def normalize(name: str) -> str:
    """Lowercases, strips common corporate suffixes and punctuation."""
    if not isinstance(name, str):
        return ""
    n = name.strip().lower()
    n = SUFFIX_PATTERN.sub("", n)
    n = re.sub(r"[^a-z0-9 ]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def canonicalize(raw_name: str, seed_list=None, threshold: int = 85):
    """Fuzzy-matches raw_name against the canonical seed list using rapidfuzz.
    Returns (canonical_name, confidence 0.0-1.0). Falls back to a cleaned-up
    title-cased version of the raw name if nothing clears the threshold, so
    every record still gets a consistent entityName instead of a raw match failure.
    """
    seed_list = seed_list or CANONICAL_SEED
    normalized_raw = normalize(raw_name)
    if not normalized_raw:
        return raw_name, 0.0

    normalized_seeds = {normalize(s): s for s in seed_list}
    match = process.extractOne(normalized_raw, list(normalized_seeds.keys()), scorer=fuzz.WRatio)

    if match and match[1] >= threshold:
        matched_key, score = match[0], match[1]
        return normalized_seeds[matched_key], round(score / 100, 2)

    fallback = " ".join(w.capitalize() for w in normalized_raw.split())
    return (fallback or raw_name), 0.0


def build_mapping_log(raw_names: list, seed_list=None, threshold: int = 85) -> pd.DataFrame:
    """Builds the Entity_Mapping_Log.csv content from a real list of raw names,
    not hand-typed examples."""
    rows, seen = [], set()
    for raw in raw_names:
        if raw in seen:
            continue
        seen.add(raw)
        canonical, confidence = canonicalize(raw, seed_list, threshold)
        rows.append({"rawName": raw, "canonicalName": canonical, "matchConfidence": confidence})

    df = pd.DataFrame(rows)
    logger.info(f"Built entity mapping log with {len(df)} unique raw names")
    return df
