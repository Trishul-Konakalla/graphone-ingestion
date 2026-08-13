# GraphOne / FrontierAtlas - Technical Architecture & Production Design

## 1. Massive Scale Strategy (500,000+ Records)
To scale data acquisition from thousands to over 500,000 records without manual intervention:
* **Distributed Worker Architecture:** Transition from single-script asyncio loops to a distributed task framework (Temporal.io or Celery) backed by Redis/RabbitMQ message queues.
* **Headless Scraping Cluster:** Route high-value or JavaScript-heavy web requests through a Playwright / Puppeteer grid behind rotating residential proxy networks (e.g., BrightData, Crawlbase) to avoid Cloudflare/Datadome captchas.
* **Stream Processing:** Stream normalized payloads directly into an S3/GCS Data Lake in Apache Parquet format prior to downstream database storage.

## 2. Resilient LLM Engine (Handling 413s & 429s)
* **DOM Pre-truncation (413 Prevention):** Strip non-semantic HTML tags (`<script>`, `<style>`, `<nav>`, `<footer>`) and retain structural prose text before passing payloads to LLMs, reducing token footprints by ~80%.
* **Multi-Tier Fallback Chain:** If the primary model fails or encounters a rate limit, the orchestrator automatically cascades requests:
  $$\text{Gemini 1.5 Flash (Primary)} \longrightarrow \text{Groq Llama-3-70B} \longrightarrow \text{DeepSeek V3}$$
* **Exponential Backoff with Jitter (429 Prevention):** Implement exponential retries with randomized jitter to prevent thundering herd problems during rate-limit events.

## 3. Freshness & Deduplication Tracking
* **Deterministic Hash Keys:** Primary keys are calculated via SHA-256 hashes of canonical entity names and source URLs ($\text{SHA256}(\text{CanonicalName} + \text{URL})$) to ensure duplicate URLs are never re-processed across distributed nodes.
* **Incremental RSS & API Polling:** Crawler nodes poll RSS feeds and job board APIs at 15-minute intervals, using HTTP `If-Modified-Since` headers to ignore unchanged content.

## 4. Primary & Graph Storage Strategy
* **Relational & Vector Database (PostgreSQL + pgvector):** Primary storage for structured entity schemas, JSON payloads, and semantic embeddings.
* **Graph Database (Neo4j / Amazon Neptune):** Graph layer mapping multi-dimensional relationships between Startups, Products, Founders, Research Papers, and associated GitHub repositories.
