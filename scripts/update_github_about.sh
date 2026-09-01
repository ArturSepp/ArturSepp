# Maintainer-run only; requires an authenticated gh CLI session.
set -euo pipefail

gh repo edit ArturSepp/QuantInvestStrats --description "Performance analytics, portfolio backtesting, risk analysis, and factsheet reporting in Python" --homepage "https://quantinveststrats.readthedocs.io"
gh repo edit ArturSepp/OptimalPortfolios --description "Production multi-asset portfolio construction and rolling backtesting in Python" --homepage "https://optimalportfolios.readthedocs.io"
gh repo edit ArturSepp/FactorLasso --description "Sparse multi-output factor-model estimation with sign constraints, prior-centered shrinkage, data-driven grouped penalties, and consistent factor covariance assembly" --homepage "https://factorlasso.readthedocs.io"
gh repo edit ArturSepp/BloombergFetch --description "Bloomberg Desktop API request/response data in pandas DataFrames for quantitative research" --homepage "https://bloombergfetch.readthedocs.io"
gh repo edit ArturSepp/StochVolModels --description "Fourier-transform pricing, Monte Carlo validation, and calibration of European options under stochastic-volatility models in Python" --homepage "https://stochvolmodels.readthedocs.io"
gh repo edit ArturSepp/TrendFollowingSystems --description "Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python for quantitative researchers and practitioners" --homepage "https://trendfollowingsystems.readthedocs.io"
gh repo edit ArturSepp/PrivateAssets --description "Multi-factor money-weighted PME for private-asset cash flows: risk-adjusted alpha and factor exposures" --homepage "https://privateassets.readthedocs.io"
gh repo edit ArturSepp/GoalBasedAllocation --description "Semi-analytical dynamic mean-variance allocation and terminal-wealth risk under regime-switching jump-diffusions" --homepage "https://goalbasedallocation.readthedocs.io"
gh repo edit ArturSepp/VanillaOptionPricers --description "Numba-vectorised Black-Scholes-Merton and Bachelier prices, Greeks, and implied-volatility fits over NumPy arrays for quantitative research pipelines" --homepage "https://vanillaoptionpricers.readthedocs.io"
gh repo edit ArturSepp/OptionChainAnalytics --description "Point-in-time option-chain containers, feed normalisation, reconstruction, and queries for quantitative research" --homepage "https://optionchainanalytics.readthedocs.io"
