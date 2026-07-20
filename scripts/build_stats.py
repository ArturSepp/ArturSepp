"""
Rebuild the Download Statistics table in README.md.

Stars/forks are fetched from the GitHub API with the workflow token and written
as STATIC shields badges (the /badge/ endpoint), so the rendered README never
depends on shields.io's shared GitHub-token pool. Download badges stay live
(pepy.tech), since they don't touch the GitHub API.
"""
import os
import re

import requests

OWNER = "ArturSepp"

# repo -> pepy/PyPI distribution slug
# Order defines the table order: mirrors the package sections in README.md
REPOS = {
    "OptimalPortfolios": "optimalportfolios",
    "factorlasso": "factorlasso",
    "QuantInvestStrats": "qis",
    "BloombergFetch": "bbg-fetch",
    "TrendFollowingSystems": "trendfollowing",
    "GoalBasedAllocation": "goal-based-allocation",
    "StochVolModels": "stochvolmodels",
    "VanillaOptionPricers": "vanilla-option-pricers",
}

HEADERS = {
    "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def row(repo: str, slug: str) -> str:
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    d = r.json()
    stars, forks = d["stargazers_count"], d["forks_count"]
    base = f"https://github.com/{OWNER}/{repo}"
    star_badge = (f"[![](https://img.shields.io/badge/stars-{stars}-blue?style=flat-square)]"
                  f"({base}/stargazers)")
    fork_badge = (f"[![](https://img.shields.io/badge/forks-{forks}-blue?style=flat-square)]"
                  f"({base}/network/members)")
    dl_total = f"[![](https://static.pepy.tech/badge/{slug})](https://pepy.tech/project/{slug})"
    dl_month = f"[![](https://static.pepy.tech/badge/{slug}/month)](https://pepy.tech/project/{slug})"
    return f"| [{repo}]({base}) | {star_badge} | {fork_badge} | {dl_total} | {dl_month} |"


def main() -> None:
    header = ("| Package | Stars | Forks | Total Downloads | Monthly |\n"
              "|---------|:-----:|:-----:|:---------------:|:-------:|")
    body = "\n".join(row(repo, slug) for repo, slug in REPOS.items())
    table = f"{header}\n{body}"

    with open("README.md", encoding="utf-8") as f:
        readme = f.read()

    block = f"<!-- STATS_START -->\n{table}\n<!-- STATS_END -->"
    new_readme, n = re.subn(r"<!-- STATS_START -->.*?<!-- STATS_END -->",
                            block, readme, flags=re.DOTALL)
    if n != 1:
        raise SystemExit("Expected exactly one STATS_START/STATS_END marker pair in README.md")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)


if __name__ == "__main__":
    main()
