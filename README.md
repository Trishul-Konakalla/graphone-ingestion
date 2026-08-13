# GraphOne / FrontierAtlas - Data Ingestion & Entity Intelligence Pipeline

Production-grade data pipeline built for GraphOne / FrontierAtlas to perform massive multi-dimensional data acquisition, 24-hour signal tracking, multi-tier LLM parsing, entity canonicalization, and structured export.

---

## Technical Features

1. **Massive Bulk Data Acquisition (Phase I):**
   * Concurrent query engine ingesting 1,000+ AI Research Papers via Arxiv API.
   * Scrapes dynamic metrics (e.g., GitHub stargazers) and structures 1,000+ Startup and Product records into unified JSON schemas.

2. **High-Fidelity Signal Ingestion (Phase II):**
   * Real-time monitoring of AI news feeds (Hacker News RSS) and AI job boards (RemoteOK API).
   * ISO-8601 date parsing ensuring strict **24-hour content freshness**.

3. **Multi-Tier LLM & Chunking Strategy (Phase III):**
   * Resilient fallback cascade: **Gemini Flash ➔ Groq Llama 3 ➔ DeepSeek**.
   * Pre-truncation DOM-density chunking to eliminate `413 Payload Too Large` errors while preserving semantic density.
   * Anti-slam exponential backoff with jitter to gracefully handle `429 Too Many Requests`.

4. **Deterministic Entity Resolution (Phase IV):**
   * Deduplication engine standardizing messy startup and product strings against canonical seed databases (e.g., `"Open AI"` ➔ `"OpenAI"`).

5. **Anti-Bot & Concurrency Architecture (Phase V & VI):**
   * Asynchronous non-blocking architecture using `asyncio` and `aiohttp`.
   * Production design for scaling to 500,000+ records via distributed queues (Temporal/Celery) and proxy clusters.

---

## Repository Structure

```text
graphone-ingestion/
├── README.md               # Pipeline overview and setup documentation
├── main.py                 # Core end-to-end Python pipeline script
├── architecture.pdf        # Detailed 3-page system design write-up
├── Startups.csv            # Extracted startup dataset (1,000 rows)
├── Products.csv            # Extracted product dataset (1,000 rows)
├── Research_Papers.csv     # Extracted research papers dataset (1,000 rows)
├── Jobs.csv                # 24-hour fresh AI jobs
├── News.csv                # 24-hour fresh AI news
└── Entity_Mapping_Log.csv  # String canonicalization & matching log
