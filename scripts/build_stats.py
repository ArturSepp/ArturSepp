"""
Rebuild the Download Statistics table and the headline totals in README.md.

Stars/forks are fetched from the GitHub API with the workflow token and written
as STATIC shields badges (the /badge/ endpoint), so the rendered README never
depends on shields.io's shared GitHub-token pool. Version badges (shields'
/pypi/v/ endpoint) and download badges (pepy.tech) stay live, since neither
touches the GitHub API.

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

import requests

OWNER = "ArturSepp"

# repo -> pepy/PyPI distribution slug, in the display order defined by GROUPS.
REPOS = {
    "QuantInvestStrats": "qis",
    "OptimalPortfolios": "optimalportfolios",
    "factorlasso": "factorlasso",
    "StochVolModels": "stochvolmodels",
    "VanillaOptionPricers": "vanilla-option-pricers",
    "OptionChainAnalytics": "option-chain-analytics",
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
        ["StochVolModels", "VanillaOptionPricers", "OptionChainAnalytics"],
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


def row(repo: str, slug: str, concept: str, stars: int, forks: int) -> str:
    """Render one table row: package, concept, PyPI version, stars, forks, total and monthly downloads."""
    base = f"https://github.com/{OWNER}/{repo}"
    version_badge = (f"[![](https://img.shields.io/pypi/v/{slug}?style=flat-square&label=&color=blue)]"
                     f"(https://pypi.org/project/{slug}/)")
    star_noun = "star" if stars == 1 else "stars"
    fork_noun = "fork" if forks == 1 else "forks"
    star_badge = (f"[![{stars} {star_noun}](https://img.shields.io/badge/{stars}-blue?style=flat-square)]"
                  f"({base}/stargazers)")
    fork_badge = (f"[![{forks} {fork_noun}](https://img.shields.io/badge/{forks}-blue?style=flat-square)]"
                  f"({base}/network/members)")
    pepy_badge = "https://static.pepy.tech/personalized-badge"
    pepy_options = "units=international_system&left_color=blue&right_color=blue&left_text="
    dl_total = (f"[![total downloads]({pepy_badge}/{slug}?period=total&{pepy_options})]"
                f"(https://pepy.tech/project/{slug})")
    dl_month = (f"[![monthly downloads]({pepy_badge}/{slug}?period=month&{pepy_options})]"
                f"(https://pepy.tech/project/{slug})")
    return f"| [{repo}]({base}) | {concept} | {version_badge} | {star_badge} | {fork_badge} | {dl_total} | {dl_month} |"


def build_blocks(counts: Dict[str, Tuple[int, int]]) -> Tuple[str, str]:
    """Return the (totals, table) markdown blocks for the given repo -> (stars, forks) map."""
    total_stars = sum(stars for stars, _ in counts.values())
    total_forks = sum(forks for _, forks in counts.values())
    star_milestone = total_stars // 1000 * 1000
    if star_milestone >= 1000 and total_stars > star_milestone:
        stars_text = f"more than {star_milestone:,} stars"
    else:
        stars_text = f"{total_stars:,} stars"
    totals = f"Together, the repositories have received {stars_text} and {total_forks:,} forks."

    header = ("| Package | Concept | Version | Stars | Forks | Total Downloads | Monthly |\n"
              "|---------|---------|:-------:|:-----:|:-----:|:---------------:|:-------:|")
    body: List[str] = []
    for group, repos in GROUPS.items():
        body.append(f"| **{group}** | | | | | | |")
        body.extend(row(repo, REPOS[repo], CONCEPTS[repo], *counts[repo]) for repo in repos)
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
