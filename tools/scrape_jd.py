"""
JD Scrape Fallback Chain
Provides domain-specific scraping strategies for job description URLs.
The agent calls Firecrawl MCP directly; this script provides the fallback logic.

Usage (from agent):
    from tools.scrape_jd import get_scrape_instructions, save_jd
    instructions = get_scrape_instructions(url)

Usage (standalone):
    python tools/scrape_jd.py <url>
"""

import sys, io, os, json, re

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass


def detect_domain(url: str) -> str:
    url_lower = url.lower()
    domain_map = [
        ("linkedin.com", "linkedin"), ("indeed.com", "indeed"),
        ("myworkdayjobs.com", "workday"), ("workday", "workday"),
        ("greenhouse.io", "greenhouse"), ("boards.greenhouse", "greenhouse"),
        ("lever.co", "lever"), ("smartrecruiters.com", "smartrecruiters"),
        ("icims.com", "icims"), ("careers.google.com", "google_careers"),
        ("google.com/about/careers", "google_careers"),
        ("jobs.apple.com", "apple"), ("amazon.jobs", "amazon"),
        ("microsoft.com/en-us/careers", "microsoft"),
        ("careers.microsoft.com", "microsoft"),
    ]
    for pattern, domain in domain_map:
        if pattern in url_lower:
            return domain
    return "generic"


DOMAIN_STRATEGIES = {
    "linkedin": {
        "description": "LinkedIn -- often behind login wall",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 5000},
        "blocked_signals": ["sign in", "join now", "log in to see", "create a free account"],
        "min_chars": 500,
    },
    "indeed": {
        "description": "Indeed -- redirects frequently",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 3000},
        "blocked_signals": ["this job has expired", "job no longer available"],
        "min_chars": 300,
    },
    "workday": {
        "description": "Workday ATS -- JavaScript-heavy, needs waitFor",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 6000},
        "blocked_signals": ["this requisition is no longer accepting applications"],
        "min_chars": 300,
    },
    "greenhouse": {
        "description": "Greenhouse ATS -- generally scrapeable",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 2000},
        "blocked_signals": ["this job is no longer available"],
        "min_chars": 300,
    },
    "lever": {
        "description": "Lever ATS -- clean HTML",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 2000},
        "blocked_signals": ["this posting is closed"],
        "min_chars": 300,
    },
    "google_careers": {
        "description": "Google Careers -- React SPA",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 5000},
        "blocked_signals": ["this job is no longer available", "404"],
        "min_chars": 400,
    },
    "generic": {
        "description": "Generic company career page",
        "scrape_params": {"formats": ["markdown"], "onlyMainContent": True, "waitFor": 3000},
        "blocked_signals": ["403", "access denied", "page not found"],
        "min_chars": 200,
    },
}


def is_content_blocked(content: str, domain: str) -> bool:
    if not content or len(content.strip()) < 100:
        return True
    strategy = DOMAIN_STRATEGIES.get(domain, DOMAIN_STRATEGIES["generic"])
    content_lower = content.lower()
    for signal in strategy.get("blocked_signals", []):
        if signal in content_lower:
            return True
    if len(content.strip()) < strategy.get("min_chars", 200):
        return True
    return False


def clean_jd_content(content: str) -> str:
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    content = re.sub(r'^\s*https?://\S+\s*$', '', content, flags=re.MULTILINE)
    return content.strip()


def get_scrape_instructions(url: str) -> dict:
    domain = detect_domain(url)
    strategy = DOMAIN_STRATEGIES.get(domain, DOMAIN_STRATEGIES["generic"])
    return {
        "url": url,
        "domain": domain,
        "description": strategy["description"],
        "recommended_params": strategy["scrape_params"],
        "blocked_signals": strategy.get("blocked_signals", []),
        "min_chars": strategy.get("min_chars", 200),
    }


def save_jd(content: str, output_folder: str) -> str:
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "job_description.txt")
    cleaned = clean_jd_content(content)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    return output_path


def write_manual_placeholder(output_folder: str, url: str) -> str:
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "job_description.txt")
    placeholder = f"MANUAL PASTE REQUIRED\n\nURL: {url}\n\n---\n\n[PASTE JD HERE]\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(placeholder)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/scrape_jd.py <url>")
        sys.exit(0)
    url = sys.argv[1]
    instructions = get_scrape_instructions(url)
    print(f"URL: {url}")
    print(f"Domain: {instructions['domain']} -- {instructions['description']}")
    print(f"Params: {json.dumps(instructions['recommended_params'], indent=2)}")
    print(f"Min chars: {instructions['min_chars']}")
