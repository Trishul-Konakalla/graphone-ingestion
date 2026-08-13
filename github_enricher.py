import asyncio
import re

import aiohttp

import config
from logging_setup import get_logger
from retry_utils import async_retry

logger = get_logger("github")

_star_cache: dict[str, int] = {}

GITHUB_REPO_RE = re.compile(r"github\.com/([^/\s]+)/([^/\s#?]+)")


def extract_owner_repo(github_url: str):
    if not github_url:
        return None
    m = GITHUB_REPO_RE.search(github_url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2).rstrip(".git")
    return owner, repo


@async_retry(max_retries=config.MAX_RETRIES, base_backoff=config.BASE_BACKOFF_SECONDS)
async def _fetch_stars(session: aiohttp.ClientSession, owner: str, repo: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    async with session.get(url, headers=headers, timeout=15) as resp:
        if resp.status == 404:
            logger.warning(f"Repo not found: {owner}/{repo}")
            return 0
        if resp.status == 403:
            raise RuntimeError("GitHub rate limit hit (403) - set GITHUB_TOKEN to raise the limit")
        resp.raise_for_status()
        data = await resp.json()
        return data.get("stargazers_count", 0)


async def get_stars(session: aiohttp.ClientSession, github_url: str, semaphore: asyncio.Semaphore) -> int:
    if not github_url:
        return 0
    if github_url in _star_cache:
        return _star_cache[github_url]

    parsed = extract_owner_repo(github_url)
    if not parsed:
        return 0
    owner, repo = parsed

    async with semaphore:
        try:
            stars = await _fetch_stars(session, owner, repo)
        except Exception as e:
            logger.error(f"Failed to fetch stars for {owner}/{repo}: {e}")
            stars = 0

    _star_cache[github_url] = stars
    return stars


async def find_github_url_for_paper(
    session: aiohttp.ClientSession, paper_title: str, semaphore: asyncio.Semaphore
) -> str:
    """Best-effort lookup of a linked GitHub repo for a paper via the Papers with Code
    search API. Returns "" if nothing is found - callers should treat that as
    'no repo linked' rather than an error."""
    query_url = "https://paperswithcode.com/api/v1/search/"
    async with semaphore:
        try:
            async with session.get(query_url, params={"q": paper_title}, timeout=15) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
                for r in data.get("results", []):
                    repo_url = (r.get("repository") or {}).get("url", "")
                    if repo_url and "github.com" in repo_url:
                        return repo_url
                return ""
        except Exception as e:
            logger.debug(f"Papers with Code lookup failed for '{paper_title[:50]}': {e}")
            return ""
