# Public package conformance

Observed: 2026-10-22T10:11:53.180385+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 35 | 2 | 2 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established |
| factormodels | 10 | 0 | 0 | 0 | checked contracts pass |
| optimalportfolios | 38 | 2 | 5 | 0 | dependency_graph: core dependency edges differ from approved registry; src/optimalportfolios/alphas/signals/run_local/signals_run.py:121: forbidden import factormodels; src/optimalportfolios/tests/factor_integration_test.py:42: forbidden import factormodels; src/optimalportfolios/tests/factor_integration_test.py:99: forbidden import factormodels; src/optimalportfolios/tests/factor_integration_test.py:139: forbidden import factormodels; src/optimalportfolios/tests/factor_integration_test.py:161: forbidden import factormodels; src/optimalportfolios/tests/factor_integration_test.py:199: forbidden import factormodels; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved |
| factorlasso | 28 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| bbg-fetch | 11 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| stochvolmodels | 17 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| trendfollowing | 13 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| privateassets | 9 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| goal-based-allocation | 13 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| vanilla-option-pricers | 11 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| option-chain-analytics | 16 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
