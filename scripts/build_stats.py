"""
Rebuild the Package Overview table and the headline totals in README.md.

Stars/forks are fetched from the GitHub API with the workflow token. Download
counts are read from Pepy's public, keyless badge endpoint. These four metrics
are written as plain links; only the PyPI version remains an image badge.

The table's group-header rows and Concept column are generated from GROUPS and
CONCEPTS below; edit them there, never in README.md, because the block is
rewritten on every run.

Two marker pairs are rewritten, both of which must be present exactly once:
  <!-- TOTALS_START --> ... <!-- TOTALS_END -->   one-line stars/forks total
  <!-- STATS_START -->  ... <!-- STATS_END -->    per-package table
"""
import os
import re
from typing import Dict, List, Tuple
from xml.etree import ElementTree

import requests

OWNER = "ArturSepp"

# repo -> pepy/PyPI distribution slug, in the display order defined by GROUPS.
REPOS = {
    "QuantInvestStrats": "qis",
    "OptimalPortfolios": "optimalportfolios",
    "factorlasso": "factorlasso",
    "StochVolModels": "stochvolmodels",
    "OptionChainAnalytics": "option-chain-analytics",
    "VanillaOptionPricers": "vanilla-option-pricers",
    "TrendFollowingSystems": "trendfollowing",
    "GoalBasedAllocation": "goal-based-allocation",
    "privateassets": "privateassets",
    "BloombergFetch": "bbg-fetch",
}

# repo -> one-line concept rendered in the table's Concept column.
CONCEPTS = {
    "QuantInvestStrats": "Performance analytics, backtesting and factsheets",
    "OptimalPortfolios": "Portfolio optimisation and rolling backtests",
    "factorlasso": "Sparse factor models with sign-constrained LASSO",
    "StochVolModels": "Stochastic volatility pricing and calibration",
    "VanillaOptionPricers": "Vectorised BSM and Bachelier pricing",
    "OptionChainAnalytics": "Point-in-time option-chain data and queries",
    "TrendFollowingSystems": "Closed-form trend-following analytics",
    "GoalBasedAllocation": "Goal-based allocation with wealth floors",
    "privateassets": "Multi-factor PME for private assets",
    "BloombergFetch": "Bloomberg data in pandas DataFrames",
}

# group title -> repos, in display order. GROUPS is the single source of truth
# for the table's order and its bold group-header rows: the block between
# STATS_START/STATS_END is rewritten on every run, so a hand-edit of the table
# in README.md is discarded at the next refresh. Change grouping and order here.
# The Package Features sections in README.md mirror this grouping and order;
# keep the two aligned when editing either.
GROUPS = {
    "Portfolio Construction, Factor Models, Backtest Reporting":
        ["QuantInvestStrats", "OptimalPortfolios", "factorlasso"],
    "Volatility and Option Modelling":
        ["StochVolModels", "OptionChainAnalytics", "VanillaOptionPricers"],
    "Dynamic Trading Strategies":
        ["TrendFollowingSystems", "GoalBasedAllocation"],
    "Illiquid Private Markets":
        ["privateassets"],
    "Data":
        ["BloombergFetch"],
}

if [repo for repos in GROUPS.values() for repo in repos] != list(REPOS) or set(CONCEPTS) != set(REPOS):
    raise SystemExit("GROUPS, REPOS and CONCEPTS must list the same repositories, "
                     "with REPOS in the order GROUPS defines")

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


def fetch_download_count(slug: str, period: str) -> str:
    """Return Pepy's compact public-badge count for ``period`` (month or total)."""
    url = f"https://static.pepy.tech/personalized-badge/{slug}"
    params = {
        "period": period,
        "units": "international_system",
        "left_text": "",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    root = ElementTree.fromstring(r.text)
    values = [
        (node.text or "").strip()
        for node in root.iter()
        if node.tag.endswith("text") and (node.text or "").strip()
    ]
    if not values:
        raise ValueError(f"Pepy badge for {slug}/{period} contained no download count")
    return values[-1]


def fetch_downloads(slug: str) -> Tuple[str, str]:
    """Return (monthly, total) public download counts for a PyPI project."""
    return fetch_download_count(slug, "month"), fetch_download_count(slug, "total")


def row(repo: str, slug: str, concept: str, stars: int, forks: int,
        monthly_downloads: str, total_downloads: str) -> str:
    """Render one table row, with only the PyPI version displayed as a badge."""
    base = f"https://github.com/{OWNER}/{repo}"
    version_badge = (f"[![](https://img.shields.io/pypi/v/{slug}?style=flat-square&label=&color=blue)]"
                     f"(https://pypi.org/project/{slug}/)")
    stars_link = f"**[{stars:,}]({base}/stargazers)**"
    forks_link = f"**[{forks:,}]({base}/network/members)**"
    downloads_url = f"https://pepy.tech/project/{slug}"
    monthly_link = f"**[{monthly_downloads}]({downloads_url})**"
    total_link = f"**[{total_downloads}]({downloads_url})**"
    return (f"| [{repo}]({base}) ({slug}) | {concept} | {version_badge} | {stars_link} | {forks_link} | "
            f"{monthly_link} | {total_link} |")


def build_blocks(counts: Dict[str, Tuple[int, int]],
                 downloads: Dict[str, Tuple[str, str]]) -> Tuple[str, str]:
    """Return the (totals, table) markdown blocks for the given repo -> (stars, forks) map."""
    total_stars = sum(stars for stars, _ in counts.values())
    total_forks = sum(forks for _, forks in counts.values())
    star_milestone = total_stars // 1000 * 1000
    if star_milestone >= 1000 and total_stars > star_milestone:
        stars_text = f"more than {star_milestone:,} stars"
    else:
        stars_text = f"{total_stars:,} stars"
    totals = f"Together, the repositories have received {stars_text} and {total_forks:,} forks."

    header = ("| Package | Concept | Version | Stars | Forks | Monthly<br>Downloads | Total<br>Downloads |\n"
              "|---------|---------|:-------:|:-----:|:-----:|:-----------------:|:---------------:|")
    body: List[str] = []
    for group, repos in GROUPS.items():
        body.append(f"| **{group}** | | | | | | |")
        body.extend(row(repo, REPOS[repo], CONCEPTS[repo], *counts[repo], *downloads[repo])
                    for repo in repos)
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
    downloads = {repo: fetch_downloads(slug) for repo, slug in REPOS.items()}
    totals, table = build_blocks(counts, downloads)

    with open("README.md", encoding="utf-8") as f:
        readme = f.read()

    readme = replace_block(readme, "TOTALS", totals)
    readme = replace_block(readme, "STATS", f"\n{table}\n")

    with open("README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
