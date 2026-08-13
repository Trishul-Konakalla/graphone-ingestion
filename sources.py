# NOTE: verify these endpoints still resolve before your run - RSS/API URLs
# occasionally move. Swap out any dead ones for an equivalent source.

NEWS_SOURCES = [
    {"name": "Hacker News", "type": "rss", "url": "https://news.ycombinator.com/rss"},
    {"name": "TechCrunch AI", "type": "rss", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "type": "rss", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "MIT Technology Review AI", "type": "rss", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "The Verge AI", "type": "rss", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
]

JOB_SOURCES = [
    {"name": "RemoteOK", "type": "json_api", "url": "https://remoteok.com/api"},
    {"name": "WeWorkRemotely Programming", "type": "rss", "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss"},
    {"name": "HN Who's Hiring", "type": "json_api", "url": "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&query=hiring"},
    {"name": "Arbeitnow", "type": "json_api", "url": "https://www.arbeitnow.com/api/job-board-api"},
    {"name": "Remotive", "type": "json_api", "url": "https://remotive.com/api/remote-jobs?category=software-dev"},
]
