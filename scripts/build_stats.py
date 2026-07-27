"""
Rebuild the Download Statistics table and the headline totals in README.md.

Stars/forks are fetched from the GitHub API with the workflow token and written
as STATIC shields badges (the /badge/ endpoint), so the rendered README never
depends on shields.io's shared GitHub-token pool. Version badges (shields'
/pypi/v/ endpoint) and download badges (pepy.tech) stay live, since neither
touches the GitHub API.

Two marker pairs are rewritten, both of which must be present exactly once:
  <!-- TOTALS_START --> ... <!-- TOTALS_END -->   one-line stars/forks total
  <!-- STATS_START -->  ... <!-- STATS_END -->    per-package table
"""
import os
import re
from typing import Dict, List, Tuple

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


def fetch_stars_forks(repo: str) -> Tuple[int, int]:
    """Return (stars, forks) for OWNER/repo from the GitHub API."""
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    d = r.json()
    return d["stargazers_count"], d["forks_count"]


def row(repo: str, slug: str, stars: int, forks: int) -> str:
    """Render one table row: package, PyPI version, stars, forks, total and monthly downloads."""
    base = f"https://github.com/{OWNER}/{repo}"
    version_badge = (f"[![](https://img.shields.io/pypi/v/{slug}?style=flat-square&label=&color=blue)]"
                     f"(https://pypi.org/project/{slug}/)")
    star_badge = (f"[![](https://img.shields.io/badge/stars-{stars}-blue?style=flat-square)]"
                  f"({base}/stargazers)")
    fork_badge = (f"[![](https://img.shields.io/badge/forks-{forks}-blue?style=flat-square)]"
                  f"({base}/network/members)")
    dl_total = f"[![](https://static.pepy.tech/badge/{slug})](https://pepy.tech/project/{slug})"
    dl_month = f"[![](https://static.pepy.tech/badge/{slug}/month)](https://pepy.tech/project/{slug})"
    return f"| [{repo}]({base}) | {version_badge} | {star_badge} | {fork_badge} | {dl_total} | {dl_month} |"


def build_blocks(counts: Dict[str, Tuple[int, int]]) -> Tuple[str, str]:
    """Return the (totals, table) markdown blocks for the given repo -> (stars, forks) map."""
    total_stars = sum(stars for stars, _ in counts.values())
    total_forks = sum(forks for _, forks in counts.values())
    totals = f"{total_stars} stars and {total_forks} forks across the {len(counts)} repositories."

    header = ("| Package | Version | Stars | Forks | Total Downloads | Monthly |\n"
              "|---------|:-------:|:-----:|:-----:|:---------------:|:-------:|")
    body: List[str] = [row(repo, REPOS[repo], *counts[repo]) for repo in REPOS]
    return totals, f"{header}\n" + "\n".join(body)


def replace_block(readme: str, marker: str, content: str) -> str:
    """Replace the single <!-- {marker}_START -->...<!-- {marker}_END --> block in readme."""
    block = f"<!-- {marker}_START -->{content}<!-- {marker}_END -->"
    new_readme, n = re.subn(rf"<!-- {marker}_START -->.*?<!-- {marker}_END -->",
                            lambda _: block, readme, flags=re.DOTALL)
    if n != 1:
        raise SystemExit(f"Expected exactly one {marker}_START/{marker}_END marker pair in README.md")
    return new_readme


def main() -> None:
    counts = {repo: fetch_stars_forks(repo) for repo in REPOS}
    totals, table = build_blocks(counts)

    with open("README.md", encoding="utf-8") as f:
        readme = f.read()

    readme = replace_block(readme, "TOTALS", totals)
    readme = replace_block(readme, "STATS", f"\n{table}\n")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
