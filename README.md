# Artur Sepp

**Quantitative Researcher & Open-Source Author | [Risk Magazine Quant of the Year 2024](https://www.risk.net/awards/7958305/quant-of-the-year-artur-sepp)**

Focused on systematic strategies, portfolio optimisation, stochastic volatility modelling, and robust statistical methods. Currently Global Head of Quantitative Analytics at [LGT Private Banking](https://www.lgt.com/). Co-originator of the Robust Optimisation of Strategic and Active Asset Allocation (ROSAA) framework and the Karasinski-Sepp log-normal beta stochastic volatility model.

For publications, speaking, and full background → [artursepp.com](https://artursepp.com)

[![Website](https://img.shields.io/badge/Website-artursepp.com-blue)](https://artursepp.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-artursepp-0077B5?logo=linkedin)](https://www.linkedin.com/in/artursepp/)
[![Twitter](https://img.shields.io/badge/Twitter-@artursepp-1DA1F2?logo=twitter)](https://twitter.com/artursepp)
[![Google Scholar](https://img.shields.io/badge/Google%20Scholar-Profile-4285F4?logo=googlescholar)](https://scholar.google.com/citations?user=UJy2xxMAAAAJ)
[![SSRN](https://img.shields.io/badge/SSRN-Author%20Page-154881)](https://ssrn.com/author=1229200)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--7038--1748-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0000-0002-7038-1748)

---

For contributors: [OSS documentation authoring standard](docs/documentation_standard.md)
covers article templates, authorship, equations, references, and reproducible analytics
across the packages.

For bounded starter tasks, review expectations and automation-assisted contributions, see
[contributing to the OSS portfolio stack](docs/contributing_to_stack.md).

## Python Packages

Over 20 years of building quantitative models — across equity, credit and rates derivatives on the sell-side, a systematic CTA, market-neutral crypto/DeFi, and now multi-asset private banking — one pattern holds: volatility regimes migrate across asset classes, and models that feel robust fail at the worst moment. These open-source packages are my working answer, spanning the full quant workflow from market data — prices, fundamentals and point-in-time option chains — to signal generation, factor modelling, and portfolio construction, through to performance measurement of private assets.

Developed alongside my published research, these packages provide runnable implementations of the methods described in the papers.

New to the ecosystem? Start with `qis` for analytics and reporting, `optimalportfolios` for portfolio construction, or `stochvolmodels` for volatility modelling.

For three offline paths using released packages, see [first workflows for the OSS portfolio stack](docs/first_steps.md): supplied weights to a factsheet, constrained allocation, and sparse factor estimation.

### Package Overview

<!-- STATS_START -->
| Package | Concept | Version | Stars | Forks | Total<br>Downloads |
|---------|---------|:-------:|:-----:|:-----:|:---------------:|
| **Portfolio Construction, Factor Models, Backtest Reporting** | | | | | |
| [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) (qis) · [Docs](https://quantinveststrats.readthedocs.io) | Performance analytics, backtesting and factsheets | [![](https://img.shields.io/pypi/v/qis?style=flat-square&label=&color=blue)](https://pypi.org/project/qis/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/QuantInvestStrats?style=flat-square&label=)](https://github.com/ArturSepp/QuantInvestStrats/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/QuantInvestStrats?style=flat-square&label=)](https://github.com/ArturSepp/QuantInvestStrats/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/qis-total-blue.svg)](https://pepy.tech/projects/qis) |
| [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) (optimalportfolios) · [Docs](https://optimalportfolios.readthedocs.io) | Portfolio optimisation and rolling backtests | [![](https://img.shields.io/pypi/v/optimalportfolios?style=flat-square&label=&color=blue)](https://pypi.org/project/optimalportfolios/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/OptimalPortfolios?style=flat-square&label=)](https://github.com/ArturSepp/OptimalPortfolios/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/OptimalPortfolios?style=flat-square&label=)](https://github.com/ArturSepp/OptimalPortfolios/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/optimalportfolios-total-blue.svg)](https://pepy.tech/projects/optimalportfolios) |
| [factorlasso](https://github.com/ArturSepp/factorlasso) (factorlasso) · [Docs](https://factorlasso.readthedocs.io) | Sparse loading estimation and factor covariance | [![](https://img.shields.io/pypi/v/factorlasso?style=flat-square&label=&color=blue)](https://pypi.org/project/factorlasso/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/factorlasso?style=flat-square&label=)](https://github.com/ArturSepp/factorlasso/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/factorlasso?style=flat-square&label=)](https://github.com/ArturSepp/factorlasso/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/factorlasso-total-blue.svg)](https://pepy.tech/projects/factorlasso) |
| [FactorModels](https://github.com/ArturSepp/FactorModels) (factormodels) · [Docs](https://github.com/ArturSepp/FactorModels/blob/main/docs/index.md) | Factor construction, point-in-time risk and GLS premia | [![](https://img.shields.io/pypi/v/factormodels?style=flat-square&label=&color=blue)](https://pypi.org/project/factormodels/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/FactorModels?style=flat-square&label=)](https://github.com/ArturSepp/FactorModels/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/FactorModels?style=flat-square&label=)](https://github.com/ArturSepp/FactorModels/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/factormodels-total-blue.svg)](https://pepy.tech/projects/factormodels) |
| **Volatility and Option Modelling** | | | | | |
| [StochVolModels](https://github.com/ArturSepp/StochVolModels) (stochvolmodels) · [Docs](https://stochvolmodels.readthedocs.io) | Stochastic volatility pricing and calibration | [![](https://img.shields.io/pypi/v/stochvolmodels?style=flat-square&label=&color=blue)](https://pypi.org/project/stochvolmodels/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/StochVolModels?style=flat-square&label=)](https://github.com/ArturSepp/StochVolModels/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/StochVolModels?style=flat-square&label=)](https://github.com/ArturSepp/StochVolModels/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/stochvolmodels-total-blue.svg)](https://pepy.tech/projects/stochvolmodels) |
| [OptionChainAnalytics](https://github.com/ArturSepp/OptionChainAnalytics) (option-chain-analytics) · [Docs](https://optionchainanalytics.readthedocs.io) | Point-in-time option-chain data and queries | [![](https://img.shields.io/pypi/v/option-chain-analytics?style=flat-square&label=&color=blue)](https://pypi.org/project/option-chain-analytics/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/OptionChainAnalytics?style=flat-square&label=)](https://github.com/ArturSepp/OptionChainAnalytics/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/OptionChainAnalytics?style=flat-square&label=)](https://github.com/ArturSepp/OptionChainAnalytics/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/option-chain-analytics-total-blue.svg)](https://pepy.tech/projects/option-chain-analytics) |
| [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) (vanilla-option-pricers) · [Docs](https://vanillaoptionpricers.readthedocs.io) | Vectorised BSM and Bachelier pricing | [![](https://img.shields.io/pypi/v/vanilla-option-pricers?style=flat-square&label=&color=blue)](https://pypi.org/project/vanilla-option-pricers/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/VanillaOptionPricers?style=flat-square&label=)](https://github.com/ArturSepp/VanillaOptionPricers/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/VanillaOptionPricers?style=flat-square&label=)](https://github.com/ArturSepp/VanillaOptionPricers/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/vanilla-option-pricers-total-blue.svg)](https://pepy.tech/projects/vanilla-option-pricers) |
| **Dynamic Trading Strategies** | | | | | |
| [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) (trendfollowing) · [Docs](https://trendfollowingsystems.readthedocs.io) | Closed-form trend-following analytics | [![](https://img.shields.io/pypi/v/trendfollowing?style=flat-square&label=&color=blue)](https://pypi.org/project/trendfollowing/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/TrendFollowingSystems?style=flat-square&label=)](https://github.com/ArturSepp/TrendFollowingSystems/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/TrendFollowingSystems?style=flat-square&label=)](https://github.com/ArturSepp/TrendFollowingSystems/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/trendfollowing-total-blue.svg)](https://pepy.tech/projects/trendfollowing) |
| [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) (goal-based-allocation) · [Docs](https://goalbasedallocation.readthedocs.io) | Goal-based allocation with wealth floors | [![](https://img.shields.io/pypi/v/goal-based-allocation?style=flat-square&label=&color=blue)](https://pypi.org/project/goal-based-allocation/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/GoalBasedAllocation?style=flat-square&label=)](https://github.com/ArturSepp/GoalBasedAllocation/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/GoalBasedAllocation?style=flat-square&label=)](https://github.com/ArturSepp/GoalBasedAllocation/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/goal-based-allocation-total-blue.svg)](https://pepy.tech/projects/goal-based-allocation) |
| **Illiquid Private Assets** | | | | | |
| [privateassets](https://github.com/ArturSepp/privateassets) (privateassets) · [Docs](https://privateassets.readthedocs.io) | Multi-factor PME for private assets | [![](https://img.shields.io/pypi/v/privateassets?style=flat-square&label=&color=blue)](https://pypi.org/project/privateassets/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/privateassets?style=flat-square&label=)](https://github.com/ArturSepp/privateassets/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/privateassets?style=flat-square&label=)](https://github.com/ArturSepp/privateassets/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/privateassets-total-blue.svg)](https://pepy.tech/projects/privateassets) |
| **Data** | | | | | |
| [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) (bbg-fetch) · [Docs](https://bloombergfetch.readthedocs.io) | Bloomberg data in pandas DataFrames | [![](https://img.shields.io/pypi/v/bbg-fetch?style=flat-square&label=&color=blue)](https://pypi.org/project/bbg-fetch/) | [![Stars](https://img.shields.io/github/stars/ArturSepp/BloombergFetch?style=flat-square&label=)](https://github.com/ArturSepp/BloombergFetch/stargazers) | [![Forks](https://img.shields.io/github/forks/ArturSepp/BloombergFetch?style=flat-square&label=)](https://github.com/ArturSepp/BloombergFetch/network/members) | [![Total downloads](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/bbg-fetch-total-blue.svg)](https://pepy.tech/projects/bbg-fetch) |
<!-- STATS_END -->

Stars, forks and versions use live badges. Total downloads use Pepy dashboard counts,
refreshed daily and rounded to thousands (K); counts below 1,000 are shown in full.
Last successful download refresh (UTC):
[![Download counts updated](https://raw.githubusercontent.com/ArturSepp/ArturSepp/automation/reports/profile-downloads/updated.svg)](https://github.com/ArturSepp/ArturSepp/blob/automation/reports/profile-downloads/counts.json).

---

<a id="one-research-workflow"></a>

## Research Workflows

The packages support two complementary research workflows. Arrows show supplied inputs, results or analytics; they do not imply a package import dependency.

### 1. Multiasset portfolio optimisation and strategies

`factormodels` defines and constructs the financial factor model, calls `factorlasso` to estimate loadings and covariance, and exposes completed model outputs for downstream use. `optimalportfolios` consumes supplied covariance and return inputs. `privateassets` can use constructed factor histories and estimates fund exposures from cash flows and NAVs. `trendfollowing` uses QIS directly for strategy analytics. QIS also provides risk analysis, backtesting and reporting across the workflow. See the [FM handoff to OP and QIS](https://github.com/ArturSepp/FactorModels/blob/main/docs/integration.md) and [private-asset workflow](https://github.com/ArturSepp/privateassets#why-privateassets).

![Multiasset workflow: QIS feeds FM and, through a separate arrow, TF. FL sits above FM and supplies statistical estimation. FM supplies risk and return inputs to OP and factor histories to privateassets. OP, privateassets and TF occupy the final column.](docs/assets/multiasset-workflow.svg?v=20261022-uniform-boxes)

### 2. Option valuation and volatility modelling

Vanilla pricing, point-in-time option chains and QIS analytics feed stochastic volatility valuation and calibration.

![Option valuation workflow: option-chain-analytics, vanilla-option-pricers and QIS each feed stochvolmodels.](docs/assets/options-workflow.svg?v=20261022-uniform-boxes)

**Optional market data:** [`bbg-fetch`](https://github.com/ArturSepp/BloombergFetch) supplies Bloomberg market data for either workflow. The stack is data-provider independent: packages accept supplied data, and `bbg-fetch` is optional throughout.

[`goal-based-allocation`](https://github.com/ArturSepp/GoalBasedAllocation) is a standalone research library within the broader ecosystem.

---

## Package Features

### Portfolio Construction, Factor Models, Backtest Reporting

`qis` supplies shared analytics; `factormodels` constructs the financial factor model and coordinates statistical estimation through `factorlasso`. `optimalportfolios` consumes prepared risk and return inputs for portfolio construction.

#### [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) (`qis`)
`qis` provides Python tools for financial-data visualisation, performance reporting, and quantitative-strategy analysis. It is the analytics and reporting engine behind `optimalportfolios`, `trendfollowing` and `option-chain-analytics`.

```bash
pip install qis
```

**Features:**
- Backtesting engine for externally computed weights with provided instrument price, carry and cost data
- Performance reporting and factsheets: risk-adjusted tables, benchmark regressions and attribution, for multi-asset, strategy, strategy vs benchmark and multi-strategy
- Visualisation layer for financial time series built on matplotlib/seaborn

#### [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) (`optimalportfolios`)
Implementation of optimisation analytics for constructing and backtesting optimal portfolios in Python. Companion code to [Sepp (2023)](https://ssrn.com/abstract=4217841) and [Sepp, Ossa & Kastenholz (2026)](https://www.pm-research.com/content/iijpormgmt/52/4/86).

```bash
pip install optimalportfolios
```

**Features:**
- Risk budgeting, alpha-focused and benchmark-constrained optimisers
- Backtesting frameworks for roll-forward analysis with handling of incomplete and missing data
- Performance attribution

#### [factorlasso](https://github.com/ArturSepp/factorlasso) (`factorlasso`)
Sparse factor model estimation with sign-constrained LASSO, prior-centred regularisation, hierarchical clustering group LASSO (HCGL) and factor-clustering group LASSO (FCGL), with integrated factor covariance assembly. Companion code to [Sepp, Ossa & Kastenholz (2026)](https://www.pm-research.com/content/iijpormgmt/52/4/86) and [Sepp, Hansen & Kastenholz (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6785958).

```bash
pip install factorlasso
```

**Features:**
- Sign-constrained LASSO and Group LASSO via CVXPY, with prior-centred regularisation (shrink toward β₀, not zero)
- Hierarchical Clustering Group LASSO (HCGL) and Factor-Clustering Group LASSO (FCGL) with auto-discovered groups
- NaN-aware estimation for variables with different history lengths
- Consistent factor covariance assembly (Σ_y = β Σ_x β' + D), scikit-learn compatible API (fit / predict / score)

#### [FactorModels](https://github.com/ArturSepp/FactorModels) (`factormodels`)
Multiasset factor construction and point-in-time risk models built on `qis` and `factorlasso`, with GLS factor premia and capital market assumption diagnostics.

```bash
pip install factormodels
```

**Features:**
- Factor definitions and construction from tradable baskets, tracked indices and observed levels
- Completed model snapshots with labelled loadings, factor, residual and asset covariance, information cutoffs and provenance
- GLS factor premia inferred from supplied forecasts, with uncertainty and capital market assumption diagnostics
- Prepared outputs for portfolio optimisation and export to QIS risk analytics; see the [completed model guide](https://github.com/ArturSepp/FactorModels/blob/main/docs/completed_model.md)

---

### Volatility and Option Modelling

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
Python implementation of vectorised pricers and implied volatility fitters for vanilla options under Black-Scholes-Merton and Bachelier models. The pricing kernel of `option-chain-analytics`.

```bash
pip install vanilla-option-pricers
```

**Features:**
- Black-Scholes-Merton log-normal and Bachelier normal option pricing
- Vectorised implied volatility fitters
- Numba-accelerated implementation

#### [OptionChainAnalytics](https://github.com/ArturSepp/OptionChainAnalytics) (`option-chain-analytics`)
Point-in-time option-chain containers, feed normalisation, chain reconstruction, queries and visualisation. The public data-container layer for empirical option research: pricing and implied-volatility inversion are delegated to `vanilla-option-pricers`, time-series and plotting utilities to `qis`.

```bash
pip install option-chain-analytics
```

**Features:**
- Timezone-aware point-in-time containers (`OptionsDataDFs`, `SlicesChain`, `ExpirySlice`) with exact-time chain reconstruction and no look-ahead
- Provider adapters behind optional extras — CBOE fitted chains, Deribit/Tardis crypto histories, ThetaData EOD equity/ETF reports, Bloomberg via `bbg-fetch` — normalised to one schema with resumable Parquet caches
- ATM-volatility and delta-skew queries, rolling vol and skew time series, and multi-page PDF chain reports

---

### Dynamic Trading Strategies

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

<a id="illiquid-private-markets"></a>

### Illiquid Private Assets

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

### Data

#### [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) (`bbg-fetch`)
`bbg-fetch` retrieves Bloomberg prices, implied volatilities, option chains, and fundamentals into pandas DataFrames through `blpapi`. It is an optional data source for the provider-independent analytics stack.

```bash
pip install bbg-fetch
```

**Features:**
- Prices, implied vols, option chains and fundamentals
- Direct `blpapi` integration
