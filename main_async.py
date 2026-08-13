import asyncio
import io
import time
import xml.etree.ElementTree as ET

import aiohttp
import feedparser
import pandas as pd

import config
from logging_setup import get_logger
from retry_utils import async_retry
from llm_orchestrator import extract_structured
from github_enricher import get_stars, find_github_url_for_paper
from entity_resolver import canonicalize, build_mapping_log
from freshness import parse_date, is_fresh
from sources import NEWS_SOURCES, JOB_SOURCES

logger = get_logger("main")

ARXIV_URL = (
    "http://export.arxiv.org/api/query?search_query=cat:cs.AI"
    "&start=0&max_results=1000&sortBy=submittedDate&sortOrder=descending"
)
YC_STARTUPS_CSV = "https://raw.githubusercontent.com/ali-ce/datasets/master/Y-Combinator/Startups.csv"

# How many papers to run GitHub star enrichment on per run - capped to respect
# GitHub's and Papers with Code's rate limits within a single demo pass.
GITHUB_ENRICH_LIMIT = 100


@async_retry(max_retries=config.MAX_RETRIES, base_backoff=config.BASE_BACKOFF_SECONDS)
async def fetch_text(session: aiohttp.ClientSession, url: str, headers: dict = None) -> str:
    async with session.get(url, headers=headers or {}, timeout=30) as resp:
        resp.raise_for_status()
        return await resp.text()


async def fetch_research_papers(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
    logger.info("Fetching research papers from Arxiv API")
    xml_text = await fetch_text(session, ARXIV_URL)
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        paper_url = entry.find("atom:id", ns).text.strip()
        published = entry.find("atom:published", ns).text.strip()
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        papers.append({
            "schemaVersion": "1.0",
            "recordType": "RESEARCH_PAPER",
            "content.title": title,
            "content.authors": ", ".join(authors),
            "content.paper_url": paper_url,
            "content.github_url": "",
            "content.github_stars": 0,
            "content.published_date": published,
        })
    logger.info(f"Fetched {len(papers)} papers")

    async def enrich(paper):
        github_url = await find_github_url_for_paper(session, paper["content.title"], semaphore)
        if github_url:
            stars = await get_stars(session, github_url, semaphore)
            paper["content.github_url"] = github_url
            paper["content.github_stars"] = stars

    await asyncio.gather(*(enrich(p) for p in papers[:GITHUB_ENRICH_LIMIT]))
    return papers


async def fetch_startups_and_products(session: aiohttp.ClientSession):
    logger.info("Fetching startups from YC dataset")
    csv_text = await fetch_text(session, YC_STARTUPS_CSV)
    df = pd.read_csv(io.StringIO(csv_text)).head(1000)

    startups, products, raw_names = [], [], []
    now_iso = pd.Timestamp.utcnow().isoformat()

    for idx, row in df.iterrows():
        raw_company = str(row.get("Company", f"Startup_{idx}"))
        website = str(row.get("Website", "https://ycombinator.com"))
        canonical_name, _ = canonicalize(raw_company)
        raw_names.append(raw_company)

        startups.append({
            "schemaVersion": "1.0",
            "recordType": "STARTUP",
            "source.name": "YCombinator Directory",
            "source.url": website,
            "content.entityName": canonical_name,
            # Left null rather than guessed - the source dataset doesn't carry
            # headcount, and the task's disqualification warning covers fabricated fields.
            "content.data.employeeCount": None,
            "collectedAt": now_iso,
        })
        products.append({
            "schemaVersion": "1.0",
            "recordType": "PRODUCT",
            "source.name": "YCombinator Directory",
            "source.url": website,
            "content.startupName": canonical_name,
            "content.pricingModel": "UNKNOWN",  # same reasoning - not present in source
            "collectedAt": now_iso,
        })

    mapping_log_df = build_mapping_log(raw_names)
    logger.info(f"Fetched {len(startups)} startups / {len(products)} products")
    return startups, products, mapping_log_df


async def fetch_news(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
    logger.info(f"Fetching news from {len(NEWS_SOURCES)} sources")
    now = pd.Timestamp.utcnow().to_pydatetime()

    async def fetch_one(src):
        async with semaphore:
            try:
                text = await fetch_text(session, src["url"], headers={"User-Agent": "Mozilla/5.0"})
            except Exception as e:
                logger.error(f"Failed to fetch news source {src['name']}: {e}")
                return []
        feed = feedparser.parse(text)
        items = []
        for entry in feed.entries:
            published_raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
            dt = parse_date(published_raw, now) if published_raw else None
            if not is_fresh(dt, hours=config.FRESHNESS_HOURS, now=now):
                continue
            items.append({
                "schemaVersion": "1.0",
                "recordType": "NEWS",
                "source.name": src["name"],
                "source.url": entry.get("link", ""),
                "content.title": entry.get("title", ""),
                "content.published_date": dt.isoformat(),
                "collectedAt": now.isoformat(),
            })
        return items

    results = await asyncio.gather(*(fetch_one(s) for s in NEWS_SOURCES))
    all_news = [item for sub in results for item in sub]
    logger.info(f"Fetched {len(all_news)} fresh (24h) news items")
    return all_news


async def fetch_jobs(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
    logger.info(f"Fetching jobs from {len(JOB_SOURCES)} sources")
    now = pd.Timestamp.utcnow().to_pydatetime()
    all_jobs = []

    async def fetch_json_source(src):
        async with semaphore:
            try:
                async with session.get(src["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=30) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            except Exception as e:
                logger.error(f"Failed to fetch job source {src['name']}: {e}")
                return None

    async def fetch_rss_source(src):
        async with semaphore:
            try:
                text = await fetch_text(session, src["url"], headers={"User-Agent": "Mozilla/5.0"})
            except Exception as e:
                logger.error(f"Failed to fetch job source {src['name']}: {e}")
                return []
        feed = feedparser.parse(text)
        items = []
        for entry in feed.entries:
            published_raw = getattr(entry, "published", None)
            dt = parse_date(published_raw, now) if published_raw else None
            if not is_fresh(dt, hours=config.FRESHNESS_HOURS, now=now):
                continue
            items.append({
                "schemaVersion": "1.0",
                "recordType": "JOB",
                "content.company": src["name"],
                "content.date": dt.isoformat(),
                "content.is_remote": True,
                "content.role_family": "Engineering",
            })
        return items

    for src in JOB_SOURCES:
        if src["type"] == "json_api":
            data = await fetch_json_source(src)
            if not data:
                continue
            entries = data[1:] if isinstance(data, list) else data.get("jobs", data.get("data", []))
            for job in entries[:200]:
                date_raw = job.get("date") or job.get("created_at") or job.get("date_posted") or job.get("publication_date")
                dt = parse_date(date_raw, now) if date_raw else None
                if not is_fresh(dt, hours=config.FRESHNESS_HOURS, now=now):
                    continue
                all_jobs.append({
                    "schemaVersion": "1.0",
                    "recordType": "JOB",
                    "content.company": job.get("company") or job.get("company_name") or src["name"],
                    "content.date": dt.isoformat(),
                    "content.is_remote": job.get("remote", True),
                    "content.role_family": "Engineering",
                })
        else:
            all_jobs.extend(await fetch_rss_source(src))

    logger.info(f"Fetched {len(all_jobs)} fresh (24h) jobs")
    return all_jobs


async def main():
    start = time.time()
    request_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        papers, (startups, products, mapping_log_df), news, jobs = await asyncio.gather(
            fetch_research_papers(session, request_semaphore),
            fetch_startups_and_products(session),
            fetch_news(session, request_semaphore),
            fetch_jobs(session, request_semaphore),
        )

    pd.DataFrame(papers).to_csv("Research_Papers.csv", index=False)
    pd.DataFrame(startups).to_csv("Startups.csv", index=False)
    pd.DataFrame(products).to_csv("Products.csv", index=False)
    pd.DataFrame(news).to_csv("News.csv", index=False)
    pd.DataFrame(jobs).to_csv("Jobs.csv", index=False)
    mapping_log_df.to_csv("Entity_Mapping_Log.csv", index=False)

    elapsed = time.time() - start
    logger.info(f"Pipeline complete in {elapsed:.1f}s")
    logger.info(
        f"Papers={len(papers)} Startups={len(startups)} Products={len(products)} "
        f"News={len(news)} Jobs={len(jobs)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
