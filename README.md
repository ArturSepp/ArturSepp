# Artur Sepp

**Quantitative Researcher & Open-Source Author | [Risk Magazine Quant of the Year 2024](https://www.risk.net/awards/7958305/quant-of-the-year-artur-sepp)**

Focused on systematic strategies, portfolio optimization, stochastic volatility modeling, and robust statistical methods. Currently Global Head of Quantitative Analytics at [LGT Private Banking](https://www.lgt.com/). Co-originator of the Robust Optimisation of Strategic and Active Asset Allocation (ROSAA) framework and the Karasinski-Sepp log-normal beta stochastic volatility model.

For publications, speaking, and full background → [artursepp.com](https://artursepp.com)

[![Website](https://img.shields.io/badge/Website-artursepp.com-blue)](https://artursepp.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-artursepp-0077B5?logo=linkedin)](https://www.linkedin.com/in/artursepp/)
[![Twitter](https://img.shields.io/badge/Twitter-@artursepp-1DA1F2?logo=twitter)](https://twitter.com/artursepp)
[![Google Scholar](https://img.shields.io/badge/Google%20Scholar-Profile-4285F4?logo=googlescholar)](https://scholar.google.com/citations?user=UJy2xxMAAAAJ)
[![SSRN](https://img.shields.io/badge/SSRN-Author%20Page-154881)](https://ssrn.com/author=1229200)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--7038--1748-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0000-0002-7038-1748)

---

## Python Packages

Over 20 years of building quantitative models — across equity, credit and rates derivatives on the sell-side, a systematic CTA, market-neutral crypto/DeFi, and now multi-asset private banking — one pattern holds: volatility regimes migrate across asset classes, and models that feel robust fail at the worst moment. These nine open-source packages are my working answer, spanning the full quant workflow from market data to signal generation, factor modeling, and portfolio construction, through to performance measurement of private assets.

Each package is developed alongside my published research — the papers ship with code you can run, and the code carries the exact methodology of the papers. <!-- TOTALS_START -->1013 stars and 185 forks across the 9 repositories.<!-- TOTALS_END -->

The packages compose into a single research workflow — market data → analytics and reporting → factor models → portfolio construction — with standalone research libraries alongside:


```mermaid
flowchart LR
    bbg["bbg-fetch<br/>Bloomberg data"] --> qis["qis<br/>analytics & reporting"]
    fl["factorlasso<br/>factor models & covariances"] --> op["optimalportfolios<br/>portfolio construction & backtesting"]
    qis --> op
    qis --> tf["trendfollowing<br/>trend-following systems"]
    fl --> pa["privateassets<br/>private-asset PME"]
    qis --> pa
```

Standalone research libraries: [`stochvolmodels`](https://github.com/ArturSepp/StochVolModels), [`vanilla-option-pricers`](https://github.com/ArturSepp/VanillaOptionPricers), [`goal-based-allocation`](https://github.com/ArturSepp/GoalBasedAllocation).

### Portfolio Construction & Factor Analytics

`factorlasso` estimates the sparse factor model and the factor covariance; `optimalportfolios` consumes them — together with the `qis` analytics engine — for portfolio construction and backtesting. `privateassets` applies the same factor machinery to private-asset cash flows, replacing single-benchmark PME with a tradable multi-factor deflator.

#### [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) (`optimalportfolios`)
Implementation of optimization analytics for constructing and backtesting optimal portfolios in Python. Companion code to [Sepp (2023)](https://ssrn.com/abstract=4217841) and [Sepp, Ossa & Kastenholz (2026)](https://www.pm-research.com/content/iijpormgmt/52/4/86).

```bash
pip install optimalportfolios
```

**Features:**
- Risk budgeting, alpha-focused and benchmark-constrained optimisers
- Backtesting frameworks for roll-forward analysis with handling of incomplete and missing data
- Performance attribution

#### [factorlasso](https://github.com/ArturSepp/factorlasso) (`factorlasso`)
Sparse factor model estimation with sign-constrained LASSO, prior-centered regularisation, hierarchical clustering group LASSO (HCGL) and factor-clustering group LASSO (FCGL), with integrated factor covariance assembly. Companion code to [Sepp, Ossa & Kastenholz (2026)](https://www.pm-research.com/content/iijpormgmt/52/4/86) and [Sepp, Hansen & Kastenholz (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6785958).

```bash
pip install factorlasso
```

**Features:**
- Sign-constrained LASSO and Group LASSO via CVXPY, with prior-centered regularisation (shrink toward β₀, not zero)
- Hierarchical Clustering Group LASSO (HCGL) and Factor-Clustering Group LASSO (FCGL) with auto-discovered groups
- NaN-aware estimation for variables with different history lengths
- Consistent factor covariance assembly (Σ_y = β Σ_x β' + D), scikit-learn compatible API (fit / predict / score)

#### [privateassets](https://github.com/ArturSepp/privateassets) (`privateassets`)
Multi-factor, money-weighted PME for private-asset cash flows: generalises Direct Alpha, KS-PME and GPME from a single benchmark to a tradable multi-factor deflator, with the classical measures shipped alongside for comparison on the same cash flows.

```bash
pip install privateassets
```

**Features:**
- Fund reporting to alpha in one call: NAV-implied returns → AR(1) unsmoothing with bootstrap bias correction → sign-constrained factor betas → multi-factor deflator → per-vintage and capital-weighted alpha with bootstrap intervals
- Point-in-time covariance with no look-ahead, enforced by tests; provenance (versions, seed, specification) travels with every result
- Classical single-benchmark measures (Direct Alpha, KS-PME, GPME) alongside the multi-factor versions

---

### Analytics & Data

#### [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) (`qis`)
Quantitative Investment Strategies (QIS) package implements Python analytics for visualisation of financial data, performance reporting, analysis of quantitative strategies. `qis` is the analytics and reporting engine behind `optimalportfolios` and `trendfollowing`.

```bash
pip install qis
```

**Features:**
- Backtesting engine for externally computed weights with provided instrument price, carry and cost data
- Performance reporting and factsheets: risk-adjusted tables, benchmark regressions and attribution, for multi-asset, strategy, strategy vs benchmark and multi-strategy
- Visualisation layer for financial time series built on matplotlib/seaborn

#### [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) (`bbg-fetch`)
Python functionality for getting different data from Bloomberg: prices, implied vols, fundamentals.

```bash
pip install bbg-fetch
```

**Features:**
- Prices, implied vols, option chains and fundamentals
- Direct `blpapi` integration

---

### Systematic Strategies & Goal-Based Allocation

#### [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) (`trendfollowing`)
Replication package for *The Science and Practice of Trend-Following Systems*. Companion code to [Sepp & Lucic (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787).

```bash
pip install trendfollowing
```

**Features:**
- Closed-form expected return, Sharpe ratio, skewness, and turnover of trend-following systems under white noise, AR(1), and ARFIMA processes, verified by Monte Carlo
- Three complete system implementations: European, American, and Time Series Momentum (TSMOM)
- 84-contract futures dataset spanning 1959–2026

#### [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) (`goal-based-allocation`)
Analytical Laplace-transform framework for dynamic mean-variance portfolio allocation under regime-switching jump-diffusions with absorbing wealth floors. Companion code to [Sepp (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6534579).

```bash
pip install goal-based-allocation
```

**Features:**
- Riccati ODE system for MV-optimal policy with regime-dependent coefficients
- Terminal wealth density decomposition (survived + floor atom + overshoot), with exact buy-and-hold moments via matrix exponential
- Investment opportunity set construction with endogenous de-risking glide paths, validated against a Monte Carlo simulator

---

### Derivatives & Volatility

#### [StochVolModels](https://github.com/ArturSepp/StochVolModels) (`stochvolmodels`)
Python implementation of pricing analytics and Monte Carlo simulations for stochastic volatility models including the Karasinski-Sepp log-normal beta SV model and the Heston model. Companion code to [Sepp & Rakhmonov (2023)](https://www.worldscientific.com/doi/10.1142/S0219024924500031) and [Sepp & Rakhmonov (2025)](https://doi.org/10.1007/s11147-025-09217-4).

```bash
pip install stochvolmodels
```

**Features:**
- Karasinski-Sepp log-normal beta SV model, with the Heston model as benchmark
- Factor Heath-Jarrow-Morton framework for rates with log-normal stochastic volatility
- Analytical valuation of European call and put options, and Monte Carlo simulations

#### [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) (`vanilla-option-pricers`)
Python implementation of vectorised pricers and implied volatility fitters for vanilla options under Black-Scholes-Merton and Bachelier models.

```bash
pip install vanilla-option-pricers
```

**Features:**
- Black-Scholes-Merton log-normal and Bachelier normal option pricing
- Vectorised implied volatility fitters
- Numba-accelerated implementation

---

### Download Statistics

<!-- STATS_START -->
| Package | Version | Stars | Forks | Total Downloads | Monthly |
|---------|:-------:|:-----:|:-----:|:---------------:|:-------:|
| [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) | [![](https://img.shields.io/pypi/v/qis?style=flat-square&label=&color=blue)](https://pypi.org/project/qis/) | [![](https://img.shields.io/badge/stars-604-blue?style=flat-square)](https://github.com/ArturSepp/QuantInvestStrats/stargazers) | [![](https://img.shields.io/badge/forks-69-blue?style=flat-square)](https://github.com/ArturSepp/QuantInvestStrats/network/members) | [![](https://static.pepy.tech/badge/qis)](https://pepy.tech/project/qis) | [![](https://static.pepy.tech/badge/qis/month)](https://pepy.tech/project/qis) |
| [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) | [![](https://img.shields.io/pypi/v/optimalportfolios?style=flat-square&label=&color=blue)](https://pypi.org/project/optimalportfolios/) | [![](https://img.shields.io/badge/stars-88-blue?style=flat-square)](https://github.com/ArturSepp/OptimalPortfolios/stargazers) | [![](https://img.shields.io/badge/forks-37-blue?style=flat-square)](https://github.com/ArturSepp/OptimalPortfolios/network/members) | [![](https://static.pepy.tech/badge/optimalportfolios)](https://pepy.tech/project/optimalportfolios) | [![](https://static.pepy.tech/badge/optimalportfolios/month)](https://pepy.tech/project/optimalportfolios) |
| [factorlasso](https://github.com/ArturSepp/factorlasso) | [![](https://img.shields.io/pypi/v/factorlasso?style=flat-square&label=&color=blue)](https://pypi.org/project/factorlasso/) | [![](https://img.shields.io/badge/stars-23-blue?style=flat-square)](https://github.com/ArturSepp/factorlasso/stargazers) | [![](https://img.shields.io/badge/forks-5-blue?style=flat-square)](https://github.com/ArturSepp/factorlasso/network/members) | [![](https://static.pepy.tech/badge/factorlasso)](https://pepy.tech/project/factorlasso) | [![](https://static.pepy.tech/badge/factorlasso/month)](https://pepy.tech/project/factorlasso) |
| [StochVolModels](https://github.com/ArturSepp/StochVolModels) | [![](https://img.shields.io/pypi/v/stochvolmodels?style=flat-square&label=&color=blue)](https://pypi.org/project/stochvolmodels/) | [![](https://img.shields.io/badge/stars-232-blue?style=flat-square)](https://github.com/ArturSepp/StochVolModels/stargazers) | [![](https://img.shields.io/badge/forks-48-blue?style=flat-square)](https://github.com/ArturSepp/StochVolModels/network/members) | [![](https://static.pepy.tech/badge/stochvolmodels)](https://pepy.tech/project/stochvolmodels) | [![](https://static.pepy.tech/badge/stochvolmodels/month)](https://pepy.tech/project/stochvolmodels) |
| [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) | [![](https://img.shields.io/pypi/v/bbg-fetch?style=flat-square&label=&color=blue)](https://pypi.org/project/bbg-fetch/) | [![](https://img.shields.io/badge/stars-18-blue?style=flat-square)](https://github.com/ArturSepp/BloombergFetch/stargazers) | [![](https://img.shields.io/badge/forks-8-blue?style=flat-square)](https://github.com/ArturSepp/BloombergFetch/network/members) | [![](https://static.pepy.tech/badge/bbg-fetch)](https://pepy.tech/project/bbg-fetch) | [![](https://static.pepy.tech/badge/bbg-fetch/month)](https://pepy.tech/project/bbg-fetch) |
| [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) | [![](https://img.shields.io/pypi/v/vanilla-option-pricers?style=flat-square&label=&color=blue)](https://pypi.org/project/vanilla-option-pricers/) | [![](https://img.shields.io/badge/stars-13-blue?style=flat-square)](https://github.com/ArturSepp/VanillaOptionPricers/stargazers) | [![](https://img.shields.io/badge/forks-9-blue?style=flat-square)](https://github.com/ArturSepp/VanillaOptionPricers/network/members) | [![](https://static.pepy.tech/badge/vanilla-option-pricers)](https://pepy.tech/project/vanilla-option-pricers) | [![](https://static.pepy.tech/badge/vanilla-option-pricers/month)](https://pepy.tech/project/vanilla-option-pricers) |
| [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) | [![](https://img.shields.io/pypi/v/trendfollowing?style=flat-square&label=&color=blue)](https://pypi.org/project/trendfollowing/) | [![](https://img.shields.io/badge/stars-20-blue?style=flat-square)](https://github.com/ArturSepp/TrendFollowingSystems/stargazers) | [![](https://img.shields.io/badge/forks-6-blue?style=flat-square)](https://github.com/ArturSepp/TrendFollowingSystems/network/members) | [![](https://static.pepy.tech/badge/trendfollowing)](https://pepy.tech/project/trendfollowing) | [![](https://static.pepy.tech/badge/trendfollowing/month)](https://pepy.tech/project/trendfollowing) |
| [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) | [![](https://img.shields.io/pypi/v/goal-based-allocation?style=flat-square&label=&color=blue)](https://pypi.org/project/goal-based-allocation/) | [![](https://img.shields.io/badge/stars-11-blue?style=flat-square)](https://github.com/ArturSepp/GoalBasedAllocation/stargazers) | [![](https://img.shields.io/badge/forks-2-blue?style=flat-square)](https://github.com/ArturSepp/GoalBasedAllocation/network/members) | [![](https://static.pepy.tech/badge/goal-based-allocation)](https://pepy.tech/project/goal-based-allocation) | [![](https://static.pepy.tech/badge/goal-based-allocation/month)](https://pepy.tech/project/goal-based-allocation) |
| [privateassets](https://github.com/ArturSepp/privateassets) | [![](https://img.shields.io/pypi/v/privateassets?style=flat-square&label=&color=blue)](https://pypi.org/project/privateassets/) | [![](https://img.shields.io/badge/stars-4-blue?style=flat-square)](https://github.com/ArturSepp/privateassets/stargazers) | [![](https://img.shields.io/badge/forks-1-blue?style=flat-square)](https://github.com/ArturSepp/privateassets/network/members) | [![](https://static.pepy.tech/badge/privateassets)](https://pepy.tech/project/privateassets) | [![](https://static.pepy.tech/badge/privateassets/month)](https://pepy.tech/project/privateassets) |
<!-- STATS_END -->
