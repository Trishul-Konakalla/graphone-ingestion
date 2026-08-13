import re
from datetime import datetime, timedelta, timezone

from dateutil import parser as dateparser

from logging_setup import get_logger

logger = get_logger("freshness")

RELATIVE_PATTERN = re.compile(r"(\d+)\s*(second|minute|hour|day)s?\s*ago", re.IGNORECASE)


def parse_date(raw: str, now: datetime = None) -> datetime | None:
    """Parses ISO-8601, RFC-822 (RSS) dates, and relative strings like '2 hours ago'.
    Returns a timezone-aware UTC datetime, or None if the string can't be parsed at all."""
    if not raw or not isinstance(raw, str):
        return None
    now = now or datetime.now(timezone.utc)
    raw = raw.strip()

    rel_match = RELATIVE_PATTERN.search(raw)
    if rel_match:
        amount, unit = int(rel_match.group(1)), rel_match.group(2).lower()
        return now - timedelta(**{f"{unit}s": amount})

    try:
        dt = dateparser.parse(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError) as e:
        logger.warning(f"Could not parse date '{raw}': {e}")
        return None


def is_fresh(raw_or_dt, hours: int = 24, now: datetime = None) -> bool:
    """True if the timestamp is within `hours` of now. Accepts either a raw date
    string or an already-parsed datetime. Items whose date can't be determined at
    all return False here - the caller is expected to apply the seen-hash
    heuristic (see main_async.py) rather than silently keeping undated items."""
    now = now or datetime.now(timezone.utc)
    dt = raw_or_dt if isinstance(raw_or_dt, datetime) else parse_date(raw_or_dt, now)
    if dt is None:
        return False
    return (now - dt) <= timedelta(hours=hours)
