# Artur Sepp

**Quantitative Researcher | [Risk Magazine Quant of the Year 2024](https://www.risk.net/awards/7958305/quant-of-the-year-artur-sepp)**

Quantitative researcher focused on systematic strategies, portfolio optimization, and stochastic volatility modeling. Currently Global Head of Quantitative Analytics at [LGT Private Banking](https://www.lgt.com/). Co-originator of the Robust Optimisation of Strategic and Active Asset Allocation (ROSAA) framework and the log-normal beta stochastic volatility model.

For publications, speaking, and full background → [artursepp.com](https://artursepp.com)

[![Website](https://img.shields.io/badge/Website-artursepp.com-blue)](https://artursepp.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-artursepp-0077B5?logo=linkedin)](https://www.linkedin.com/in/artursepp/)
[![Twitter](https://img.shields.io/badge/Twitter-@artursepp-1DA1F2?logo=twitter)](https://twitter.com/artursepp)
[![Google Scholar](https://img.shields.io/badge/Google%20Scholar-Profile-4285F4?logo=googlescholar)](https://scholar.google.com/citations?user=UJy2xxMAAAAJ&hl=en)
[![SSRN](https://img.shields.io/badge/SSRN-Author%20Page-154881)](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=1229200)
[![Email](https://img.shields.io/badge/Email-artursepp@gmail.com-red)](mailto:artursepp@gmail.com)

---

## Python Packages

### [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) (`qis`)
Quantitative Investment Strategies (QIS) package implements Python analytics for visualisation of financial data, performance reporting, analysis of quantitative strategies.

**Features:**
- Financial data visualization
- Performance reporting and analytics  
- Quantitative strategy analysis
- Portfolio construction tools

### [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) (`optimalportfolios`)
Implementation of optimization analytics for constructing and backtesting optimal portfolios in Python. Companion code to [Sepp (2023)](https://ssrn.com/abstract=4217841) and [Sepp, Ossa & Kastenholz (2026)](https://www.pm-research.com/content/iijpormgmt/52/4/86)

**Features:**
- Portfolio optimization algorithms
- Risk budgeting implementation
- Backtesting frameworks
- Performance attribution

### [StochVolModels](https://github.com/ArturSepp/StochVolModels) (`stochvolmodels`)
Python implementation of pricing analytics and Monte Carlo simulations for stochastic volatility models including Karasinski-Sepp log-normal stochastic volatility model and Heston volatility model. Companion code to [Sepp & Rakhmonov (2023)](https://www.worldscientific.com/doi/10.1142/S0219024924500031).

**Features:**
- Karasinski-Sepp log-normal stochastic volatility model
- Heston model
- Monte Carlo simulations
- Analytical valuation of European call and put options

### [factorlasso](https://github.com/ArturSepp/factorlasso) (`factorlasso`)
Sparse factor model estimation with sign-constrained LASSO, prior-centered regularisation, and hierarchical group LASSO (HCGL) with integrated factor covariance assembly. Companion code to [Sepp, Ossa & Kastenholz (2026)](https://www.pm-research.com/content/iijpormgmt/52/4/86) and [Sepp, Hansen & Kastenholz (2026)].

**Features:**
- Sign-constrained LASSO and Group LASSO via CVXPY
- Prior-centered regularisation (shrink toward β₀, not zero)
- Hierarchical Clustering Group LASSO (HCGL) with auto-discovered groups
- NaN-aware estimation for variables with different history lengths
- Consistent factor covariance assembly (Σ_y = β Σ_x β' + D)
- scikit-learn compatible API (fit / predict / score)
- 
**Features:**
- Sign-constrained LASSO and Group LASSO via CVXPY
- Prior-centered regularisation (shrink toward β₀, not zero)
- Hierarchical Clustering Group LASSO (HCGL) with auto-discovered groups
- NaN-aware estimation for variables with different history lengths
- Consistent factor covariance assembly (Σ_y = β Σ_x β' + D)
- scikit-learn compatible API (fit / predict / score)

### [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) (`bbg-fetch`)
Python functionality for getting different data from Bloomberg: prices, implied vols, fundamentals.

**Features:**
- Bloomberg data fetching wrapper
- Price data retrieval
- Implied volatility data
- Fundamental data access
- Built on xbbg package integration

### [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) (`vanilla-option-pricers`)
Python implementation of vectorised pricers for vanilla options

**Features:**
- Black-Scholes log-normal option pricing
- Bachelier normal option pricing

### [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) (`goal-based-allocation`)
Analytical Laplace-transform framework for dynamic mean-variance portfolio allocation under regime-switching jump-diffusions with absorbing wealth floors. Companion code to [Sepp (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6534579).

**Features:**
- Riccati ODE system for MV-optimal policy with regime-dependent coefficients
- Terminal wealth density decomposition (survived + floor atom + overshoot)
- Exact buy-and-hold moments via matrix exponential
- Investment opportunity set construction with endogenous de-risking glide paths
- Monte Carlo simulator for validation

### Download Statistics

| Package | Stars | Forks | Total Downloads | Monthly |
|---------|:-----:|:-----:|:---------------:|:-------:|
| [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) | [![](https://img.shields.io/github/stars/ArturSepp/QuantInvestStrats?style=flat-square)](https://github.com/ArturSepp/QuantInvestStrats) | [![](https://img.shields.io/github/forks/ArturSepp/QuantInvestStrats?style=flat-square)](https://github.com/ArturSepp/QuantInvestStrats) | [![](https://static.pepy.tech/badge/qis)](https://pepy.tech/project/qis) | [![](https://static.pepy.tech/badge/qis/month)](https://pepy.tech/project/qis) |
| [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) | [![](https://img.shields.io/github/stars/ArturSepp/OptimalPortfolios?style=flat-square)](https://github.com/ArturSepp/OptimalPortfolios) | [![](https://img.shields.io/github/forks/ArturSepp/OptimalPortfolios?style=flat-square)](https://github.com/ArturSepp/OptimalPortfolios) | [![](https://static.pepy.tech/badge/optimalportfolios)](https://pepy.tech/project/optimalportfolios) | [![](https://static.pepy.tech/badge/optimalportfolios/month)](https://pepy.tech/project/optimalportfolios) |
| [StochVolModels](https://github.com/ArturSepp/StochVolModels) | [![](https://img.shields.io/github/stars/ArturSepp/StochVolModels?style=flat-square)](https://github.com/ArturSepp/StochVolModels) | [![](https://img.shields.io/github/forks/ArturSepp/StochVolModels?style=flat-square)](https://github.com/ArturSepp/StochVolModels) | [![](https://static.pepy.tech/badge/stochvolmodels)](https://pepy.tech/project/stochvolmodels) | [![](https://static.pepy.tech/badge/stochvolmodels/month)](https://pepy.tech/project/stochvolmodels) |
| [factorlasso](https://github.com/ArturSepp/factorlasso) | [![](https://img.shields.io/github/stars/ArturSepp/factorlasso?style=flat-square)](https://github.com/ArturSepp/factorlasso) | [![](https://img.shields.io/github/forks/ArturSepp/factorlasso?style=flat-square)](https://github.com/ArturSepp/factorlasso) | [![](https://static.pepy.tech/badge/factorlasso)](https://pepy.tech/project/factorlasso) | [![](https://static.pepy.tech/badge/factorlasso/month)](https://pepy.tech/project/factorlasso) |
| [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) | [![](https://img.shields.io/github/stars/ArturSepp/BloombergFetch?style=flat-square)](https://github.com/ArturSepp/BloombergFetch) | [![](https://img.shields.io/github/forks/ArturSepp/BloombergFetch?style=flat-square)](https://github.com/ArturSepp/BloombergFetch) | [![](https://static.pepy.tech/badge/bbg-fetch)](https://pepy.tech/project/bbg-fetch) | [![](https://static.pepy.tech/badge/bbg-fetch/month)](https://pepy.tech/project/bbg-fetch) |
| [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) | [![](https://img.shields.io/github/stars/ArturSepp/VanillaOptionPricers?style=flat-square)](https://github.com/ArturSepp/VanillaOptionPricers) | [![](https://img.shields.io/github/forks/ArturSepp/VanillaOptionPricers?style=flat-square)](https://github.com/ArturSepp/VanillaOptionPricers) | [![](https://static.pepy.tech/badge/vanilla-option-pricers)](https://pepy.tech/project/vanilla-option-pricers) | [![](https://static.pepy.tech/badge/vanilla-option-pricers/month)](https://pepy.tech/project/vanilla-option-pricers) |
| [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) | [![](https://img.shields.io/github/stars/ArturSepp/GoalBasedAllocation?style=flat-square)](https://github.com/ArturSepp/GoalBasedAllocation) | [![](https://img.shields.io/github/forks/ArturSepp/GoalBasedAllocation?style=flat-square)](https://github.com/ArturSepp/GoalBasedAllocation) | [![](https://static.pepy.tech/badge/goal-based-allocation)](https://pepy.tech/project/goal-based-allocation) | [![](https://static.pepy.tech/badge/goal-based-allocation/month)](https://pepy.tech/project/goal-based-allocation) |
