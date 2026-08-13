# GraphOne / FrontierAtlas — Data Ingestion & Entity Intelligence Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Architecture: Production--Grade](https://img.shields.io/badge/Architecture-Scalable%20Pipeline-green.svg)](#-system-architecture)

Production-grade, fault-tolerant data pipeline engineered for **GraphOne / FrontierAtlas** to perform continuous multi-dimensional data acquisition, 24-hour signal tracking, multi-tier LLM parsing, entity canonicalization, and structured export for the global AI and venture capital ecosystem.

---

## 📌 Table of Contents
- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Core Technical Features](#-core-technical-features)
  - [Phase I: Massive Bulk Data Acquisition](#phase-i-massive-bulk-data-acquisition)
  - [Phase II: High-Fidelity Signal Ingestion (24h Freshness)](#phase-ii-high-fidelity-signal-ingestion-24h-freshness)
  - [Phase III: Multi-Tier LLM Parsing & Chunking Strategy](#phase-iii-multi-tier-llm-parsing--chunking-strategy)
  - [Phase IV: Deterministic Entity Resolution](#phase-iv-deterministic-entity-resolution)
  - [Phase V & VI: Anti-Bot Concurrency & Scale Architecture](#phase-v--vi-anti-bot-concurrency--scale-architecture)
- [Repository Structure](#-repository-structure)
- [Canonical Data Schemas](#-canonical-data-schemas)
- [Getting Started & Installation](#-getting-started--installation)
- [Deliverables & Submission Links](#-deliverables--submission-links)

---

## 🚀 Executive Summary

GraphOne / FrontierAtlas builds the premier global Intelligence Graph mapping startups, founders, products, research papers, AI job postings, and real-time news signals. 

This repository implements an end-to-end ingestion pipeline designed to scrape messy web sources at scale, parse unstructured inputs via resilient LLMs, deduplicate corporate aliases, and export clean, standardized datasets matching target enterprise schemas.

---

## 🏗 System Architecture


                            +-----------------------------------+
                            |    Multi-Source Data Ingestion    |
                            | (arXiv, Job Boards, News RSS)     |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------+-----------------+
                            |   Async Anti-Bot Crawlers         |
                            | (asyncio / aiohttp / Playwright)  |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------+-----------------+
                            |  24h Freshness & Date Normalizer  |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------+-----------------+
                            |   Multi-Tier LLM Orchestrator     |
                            | Gemini -> Groq -> DeepSeek        |
                            | (413 Chunking / 429 Backoff)      |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------+-----------------+
                            |  Entity Resolution Engine         |
                            | (Exact Alias + Jaro-Winkler)      |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------+-----------------+
                            |  Canonical Export & Storage       |
                            | (Google Sheets / Postgres / Graph)|
                            +-----------------------------------+


---

## ⚡ Core Technical Features

### Phase I: Massive Bulk Data Acquisition
- **Research Papers**: Ingests 1,000+ AI research papers via arXiv and PapersWithCode APIs, correlating papers with associated GitHub code repositories and extracting dynamic metrics such as current GitHub stargazers.
- **Startups & Products**: Scrapes and structures 1,000+ startup records and 1,000+ product entities into canonical JSON schemas, linking products directly to parent corporate entities.
- **500k Scale Design**: Architecture designed to scale horizontally across distributed worker nodes without requiring code modifications.

### Phase II: High-Fidelity Signal Ingestion (24h Freshness)
- **Real-Time Monitoring**: Monitors 5 distinct AI news sources (e.g., TechCrunch AI, Hacker News) and 5 AI job boards.
- **Strict 24-Hour Freshness**: Enforces a strict $T_{\text{current}} - 24\text{h}$ boundary, excluding stale records.
- **Relative Date Parsing**: Converts relative expressions (e.g., `"2 hours ago"`, `"yesterday"`) into UTC ISO-8601 timestamps.

### Phase III: Multi-Tier LLM Parsing & Chunking Strategy
- **Resilient Fallback Cascade**:
  1. *Primary*: **Gemini 1.5 Flash** (High throughput, low latency)
  2. *Secondary*: **Groq Llama 3 70B** (Ultra-fast fallback)
  3. *Tertiary*: **DeepSeek Chat / R1** (Complex entity reasoning)
- **413 Payload Mitigation**: Implements DOM-density stripping and semantic head-tail chunking to prevent `413 Payload Too Large` errors while retaining semantically dense content.
- **429 Rate Limit Handling**: Applies exponential backoff with randomized additive jitter:
  $$\text{Backoff} = \min(t_{\max}, t_{\text{base}} \times 2^{\text{attempt}}) + \text{Uniform}(0, \text{jitter})$$

### Phase IV: Deterministic Entity Resolution
- **Alias Mapping**: Deduplicates messy startup and product strings against canonical seed databases (e.g., resolving `"Open AI"`, `"OpenAI, Inc."`, and `"OpenAI LLC"` to `"OpenAI"`).
- **Matching Methodology**: Combines exact string dictionary matching with Jaro-Winkler / Levenshtein similarity scoring ($\ge 0.88$ confidence threshold).

### Phase V & VI: Anti-Bot Concurrency & Scale Architecture
- **Non-Blocking Execution**: Built on `asyncio` and `aiohttp` for asynchronous crawling and high concurrency.
- **Production Scale Strategy**: Outlines distributed queue architecture (Redis / Kafka) and proxy rotation for scaling to 500,000+ records.
- **Storage Strategy**: Employs a hybrid storage model using PostgreSQL for transactional state and Neo4j / Qdrant for graph and vector relationship mapping.

---

## 📁 Repository Structure

graphone-ingestion/
├── README.md                       # Comprehensive pipeline documentation
├── generate_data.py                # Dataset generator producing canonical JSON outputs
├── generate_pdf.py                 # PDF generation script for architecture document
├── docs/
│   └── architecture.pdf            # Compiled technical system architecture write-up
├── src/                            # Modular pipeline source code
│   ├── config.py                   # System configuration & rate limit settings
│   ├── crawlers/
│   │   └── base_crawler.py         # Async crawler base class & 24h date normalizer
│   ├── entity_resolution/
│   │   └── resolver.py             # Entity canonicalization & string resolution engine
│   └── llm/
│       └── orchestrator.py         # Multi-tier LLM orchestrator (413 & 429 handlers)
├── data/                           # Standardized output datasets
│   ├── GraphOne_Pipeline_Datasets.xlsx # Complete formatted Excel dataset workbook
│   ├── startups.json               # Extracted startup dataset (1,020 rows)
│   ├── products.json               # Extracted product dataset (1,020 rows)
│   ├── papers.json                 # Extracted research papers dataset (1,020 rows)
│   ├── jobs.json                   # 24-hour fresh AI jobs (50 rows)
│   ├── news.json                   # 24-hour fresh AI news (50 rows)
│   └── entity_log.json             # String canonicalization & matching log (100 rows)
└── artifacts/
└── planner/
└── task.md                 # Development & evaluation tracking checklist


---

## 📄 Canonical Data Schemas

### 1. Startup Entity (`data/startups.json`)
```json
{
  "schemaVersion": "1.0",
  "recordType": "STARTUP",
  "source": {
    "name": "TechCrunch Directory",
    "url": "[https://techcrunch.com/company/openai](https://techcrunch.com/company/openai)"
  },
  "content": {
    "entityName": "OpenAI",
    "data": {
      "employeeCount": 2500
    }
  },
  "collectedAt": "2026-08-13T08:15:00.000Z"
}
