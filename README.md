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
