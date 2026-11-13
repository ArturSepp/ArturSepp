# Public package conformance

Observed: 2026-11-13T13:07:37.289166+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 48 | 3 | 2 | 0 | dependency_graph: missing import bans: factormodels; src/qis/fx/run_local/fx_rates_data_run.py:111: forbidden import bbg_fetch; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established |
| factormodels | 11 | 3 | 0 | 0 | action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github_about: homepage |
| optimalportfolios | 47 | 2 | 5 | 0 | action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved |
| factorlasso | 32 | 2 | 0 | 0 | action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| bbg-fetch | 11 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| stochvolmodels | 18 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| trendfollowing | 13 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| privateassets | 9 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| goal-based-allocation | 13 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| vanilla-option-pricers | 12 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |
| option-chain-analytics | 18 | 3 | 0 | 0 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml |

Recorded runtime licence review: **unknown** — No runtime evidence supplied; source metadata checks do not establish a runtime licence claim.

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
