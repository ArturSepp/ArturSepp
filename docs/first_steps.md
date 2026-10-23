# First workflows for the OSS portfolio stack

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Choose a task and run an offline example with a released package. These three workflows
connect supplied portfolio weights, constrained allocation and sparse factor estimation.

| Your task | Start here | Visible result |
|---|---|---|
| Evaluate weights you already have | [qis factsheet](#supplied-weights-to-a-qis-factsheet) | Portfolio history, performance table and a PDF factsheet |
| Build allocations with portfolio constraints | [OptimalPortfolios allocation](#constrained-multi-asset-allocation) | Six-asset target weights and portfolio NAV |
| Estimate exposures from factor and asset returns | [FactorLasso estimation](#sparse-factor-estimation) | Loadings, selected penalty, residual checks and volatility decomposition |

QIS owns holdings simulation and reporting. OptimalPortfolios owns the allocation decisions
and uses QIS for simulation. FactorLasso owns the statistical estimation; its covariance
results can supply OP's factor-estimation workflow.

The release snapshot used here is **qis 5.37.0, optimalportfolios 7.21.0 and factorlasso 1.0.4**,
retrieved on 16 October 2026. These are the versions to use for this walkthrough.
Package sources and software citations are linked at the end.

## Install and save the examples

Use Python 3.12. The commands below are for PowerShell; keep the environment and working
folder outside OneDrive or another synchronized directory.

~~~powershell
py -3.12 -m venv C:\Python\OSSFirstUse312
$python = 'C:\Python\OSSFirstUse312\Scripts\python.exe'
New-Item -ItemType Directory -Path C:\OSSFirstUse -Force | Out-Null
Set-Location C:\OSSFirstUse
& $python -m pip install 'qis==5.37.0' 'optimalportfolios==7.21.0' 'factorlasso==1.0.4'
if ($LASTEXITCODE -ne 0) { throw 'Package installation failed' }
& $python -c "from importlib.metadata import version; print({p: version(p) for p in ('qis', 'optimalportfolios', 'factorlasso')})"
~~~

Install the core packages without extras. The examples use synthetic data or a bundled
fixture; no vendor credentials are required. Installation and the following downloads
need internet access. After that setup, all three analytical workflows run offline.

Save the existing examples from their pinned public source revisions:

~~~powershell
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ArturSepp/QuantInvestStrats/98bdae18d8001f29d1054f53cc9ad663d15200df/examples/getting_started/offline_quickstart.py' -OutFile qis_quickstart.py
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ArturSepp/OptimalPortfolios/f1fcd0b20d3be0456884bea6fef59a5f19195187/examples/getting_started/production_quickstart.py' -OutFile op_quickstart.py
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ArturSepp/FactorLasso/66aba40c931b249dfac82c197a4b839e7d4eca12/examples/docs/quickstart.py' -OutFile factorlasso_quickstart.py
~~~

These scripts remain owned by their packages. The pinned copies let this walkthrough
reuse the same code without requiring a repository checkout.

## Supplied weights to a qis factsheet

The [existing offline quickstart](https://github.com/ArturSepp/QuantInvestStrats/blob/98bdae18d8001f29d1054f53cc9ad663d15200df/examples/getting_started/offline_quickstart.py)
supplies 50% US equities, 30% Treasury bonds and 20% emerging-market equities to QIS.
Its seeded business-day price panel spans 2018-01-02 through 2025-12-31. The emerging-market
series starts late; the quarterly target schedule allocates over instruments available
at each decision date.

A target at date t sets units at that close. Those units earn the next holding-period
return and remain fixed until a rebalance, allowing weights to drift. Costs are 0.001,
or 10 basis points of absolute traded notional. This example uses zero implementation
lag. The performance table uses monthly simple returns and arithmetic Sharpe with rf=0;
the continuation below explicitly selects the same Sharpe column and legend.

Save the following short continuation as `qis_factsheet.py` beside `qis_quickstart.py`:

~~~python
"""Make a monthly strategy factsheet from the existing offline qis quickstart."""
from importlib.metadata import version
from pathlib import Path
import runpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import qis

print(f"qis {version('qis')}")
context = runpy.run_path(str(Path(__file__).with_name("qis_quickstart.py")))
figures = qis.factsheet(
    context["portfolio_data"], benchmark_prices=context["benchmark_nav"],
    reporting_frequency="monthly", add_rates_data=False,
    perf_params=context["perf_params"],
    perf_columns=[qis.PerfStat.PA_RETURN, qis.PerfStat.VOL,
                  qis.PerfStat.SHARPE_ARITH, qis.PerfStat.MAX_DD],
    perf_stats_labels=[qis.PerfStat.PA_RETURN, qis.PerfStat.VOL,
                       qis.PerfStat.SHARPE_ARITH],
    factsheet_name="Synthetic supplied-weight portfolio",
)

assert figures and all(isinstance(figure, plt.Figure) for figure in figures)
output = Path("qis_factsheet.pdf").resolve()
with PdfPages(output) as pdf:
    for figure in figures:
        pdf.savefig(figure, bbox_inches="tight")
print(f"Saved {len(figures)} factsheet page(s): {output}")
plt.show()
for figure in figures:
    plt.close(figure)
~~~

Run it:

~~~powershell
& $python qis_factsheet.py | Tee-Object qis_result.txt
if ($LASTEXITCODE -ne 0) { throw 'QIS workflow failed' }
~~~

Open `qis_factsheet.pdf`. It shows the portfolio history, monthly returns, drawdowns,
exposures, turnover and costs. The console also reports the target schedule and
benchmark-relative tracking error. The PDF is saved before any interactive figure window
opens; close the figure window to finish the script.

The first use can take longer while Numba compiles numerical kernels. A later call in the
same Python process can reuse compiled functions; a later process may reuse the disk cache.
Measure these cases separately. For a headless machine, set `$env:MPLBACKEND='Agg'` before
running; use the saved PDF as the visible result.

Next: change `STATIC_WEIGHTS` in the saved canonical script to your supplied targets,
then follow [factsheets and reporting](https://quantinveststrats.readthedocs.io/en/stable/factsheets_and_reporting.html)
for report choices. Use the OP path below when you need the library to construct targets.

## Constrained multi asset allocation

Run the [existing production quickstart](https://github.com/ArturSepp/OptimalPortfolios/blob/f1fcd0b20d3be0456884bea6fef59a5f19195187/examples/getting_started/production_quickstart.py):

~~~powershell
& $python op_quickstart.py | Tee-Object op_result.txt
if ($LASTEXITCODE -ne 0) { throw 'Allocation workflow failed' }
~~~

The packaged monthly fixture covers six assets: global bonds, US Treasuries, high-yield
bonds, world equities, hedge funds and commodities. Prices span 2010-01-31 through
2022-12-31. Monthly log returns feed an EWMA covariance estimator with span 24; the
covariance is annualized by 12.

The minimum-variance targets are long-only, sum to one and cap every asset at 35%.
Quarter-end decisions run from 2015-03-31 to 2022-09-30. QIS implements each decision one
observation later: one **month** for this monthly price panel. Units then drift between
trades, with 10 basis points charged on absolute traded notional.

The console and `op_result.txt` show **31 decision dates by six assets**, the last target
weights and final NAV. Solver-dependent last weights may vary slightly across dependency
versions; use the constraints and dimensions to understand the result.

For a hosted route, [open the existing Colab notebook](https://colab.research.google.com/github/ArturSepp/OptimalPortfolios/blob/main/examples/getting_started/production_quickstart.ipynb).
Its Python cell mirrors the canonical script and its setup displays the installed version.
Colab installs the latest release, so it can differ from this pinned local walkthrough.

Next: [the allocation quickstart](https://optimalportfolios.readthedocs.io/en/stable/quickstart.html)
explains the solver, timing and cost checks. The
[constraints guide](https://optimalportfolios.readthedocs.io/en/stable/constraints.html)
shows which portfolio choices you can change.

## Sparse factor estimation

Run the [existing FactorLasso quickstart](https://github.com/ArturSepp/FactorLasso/blob/66aba40c931b249dfac82c197a4b839e7d4eca12/examples/docs/quickstart.py):

~~~powershell
& $python factorlasso_quickstart.py | Tee-Object factorlasso_result.txt
if ($LASTEXITCODE -ne 0) { throw 'Factor estimation workflow failed' }
~~~

The script draws 120 monthly observations of 12 synthetic funds on four factors, with
fixed seed 20260921. Inputs are decimal monthly returns. Four expanding-window folds
select the regularization penalty for hierarchical-cluster group LASSO with derived
sign constraints. CLARABEL solves the convex fits.

The output includes a **12 by four loading table**, the selected penalty and held-out
score, residual diagnostics and annualized volatility decomposition. Covariance assembly
multiplies monthly covariance and residual variance by 12. The final refit uses all 120
observations to describe that sample; it is not a rolling investment backtest.

The script checks predictions, R-squared and covariance assembly against independent
NumPy calculations. These assertions describe this fixed teaching sample, not expected
performance on market data.

Next: [the full FactorLasso quickstart](https://github.com/ArturSepp/factorlasso/blob/66aba40c931b249dfac82c197a4b839e7d4eca12/docs/quickstart.md)
explains each result. For portfolio use, follow
[factor covariance assembly](https://github.com/ArturSepp/factorlasso/blob/66aba40c931b249dfac82c197a4b839e7d4eca12/docs/factor_covariance_assembly.md)
and OP's [covariance estimator guide](https://optimalportfolios.readthedocs.io/en/stable/covariance_estimators.html).

## Package sources and citations

| Package | Repository | Software citation |
|---|---|---|
| qis | [QuantInvestStrats](https://github.com/ArturSepp/QuantInvestStrats) | [CITATION.cff](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff) |
| optimalportfolios | [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) | [CITATION.cff](https://github.com/ArturSepp/OptimalPortfolios/blob/main/CITATION.cff) |
| factorlasso | [FactorLasso](https://github.com/ArturSepp/factorlasso) | [CITATION.cff](https://github.com/ArturSepp/factorlasso/blob/main/CITATION.cff) |

For a broader comparison of allocation-library workflows, see OP's
[package comparison](https://optimalportfolios.readthedocs.io/en/stable/package_comparison.html).

## More task-specific workflows

The three portfolio workflows above remain the original pilot. The following package-owned
entry points were checked separately on Python 3.12 on 17 October 2026. Follow one guide
and install its recorded release in its own C-local environment; no combined installation is
required. These are exercised workflow floors, not historical feature-introduction versions.
Installation/downloads need internet access; calculations use synthetic or packaged inputs.
The linked source pages and hosted builds may differ until publication.

| Your task / owner | Verified release | Guide | Visible result and boundary |
|---|---|---|---|
| Price vanilla options and invert implied volatility (`vanilla-option-pricers`) | 2.2.1 | [First workflow](https://github.com/ArturSepp/VanillaOptionPricers/blob/main/docs/getting_started.md) | BSM/Bachelier arrays, implied-volatility round trips and parity |
| Compare closed-form trend-following risk/return (`trendfollowing`) | 1.3.1 | [First workflow](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/docs/quickstart.md) | Two fixed-parameter autocorrelation models; no realised-strategy backtest |
| Evaluate cashflows with public-market equivalents (`privateassets`) | 0.7.1 | [First workflow](https://github.com/ArturSepp/PrivateAssets/blob/main/docs/quickstart.rst) | Synthetic cashflows, a supplied benchmark and dimensionless PME; factors extra is separate |
| Explore a goal-based allocation under regime switching (`goal-based-allocation`) | 0.4.2 | [First workflow](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/docs/getting-started.md) | Terminal wealth, floor and survival diagnostics; source draft values may differ even at the same version string |
| Price a fixed LogSV model (`stochvolmodels`) | 2.5.0 | [First workflow](https://github.com/ArturSepp/StochVolModels/blob/main/docs/getting_started.md) | One European option and a quote-free two-maturity chain; research extra is separate |
| Reconstruct and query a synthetic option chain (`option-chain-analytics`) | 5.3.0 | [First workflow](https://github.com/ArturSepp/OptionChainAnalytics/blob/main/docs/first_success.md) | Exact observation selection, front ATM strike/volatility and weekly roll expiry; provider extras are separate |
| Check installation and synthetic response-shaped inputs (`bbg-fetch`) | 3.2.1 | [First workflow](https://github.com/ArturSepp/BloombergFetch/blob/main/docs/first_success.rst) | Synthetic put-call-parity forward/rate; the real blpapi SDK is required, Bloomberg connection is NOT TESTED |

For each package, use the guide's pinned canonical script and separate setup time from
execution time. Do not infer profitability, forecasting skill, live provider access or a
universal runtime from a deterministic teaching result. Core QIS/OP/FactorLasso dependency
direction remains unchanged. The Bloomberg route requires the genuine SDK from its official
index before import; no credential or Terminal session is needed for the synthetic check.

Package sources and citations for these routes:

- [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) and [CITATION.cff](https://github.com/ArturSepp/VanillaOptionPricers/blob/main/CITATION.cff).
- [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) and [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
- [PrivateAssets](https://github.com/ArturSepp/PrivateAssets) and [CITATION.cff](https://github.com/ArturSepp/PrivateAssets/blob/main/CITATION.cff).
- [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) and [CITATION.cff](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/CITATION.cff).
- [StochVolModels](https://github.com/ArturSepp/StochVolModels) and [CITATION.cff](https://github.com/ArturSepp/StochVolModels/blob/main/CITATION.cff).
- [OptionChainAnalytics](https://github.com/ArturSepp/OptionChainAnalytics) and [CITATION.cff](https://github.com/ArturSepp/OptionChainAnalytics/blob/main/CITATION.cff).
- [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) and [CITATION.cff](https://github.com/ArturSepp/BloombergFetch/blob/main/CITATION.cff).
