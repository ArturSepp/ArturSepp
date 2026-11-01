# Public package conformance

Observed: 2026-11-01T07:48:43.006849+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 39 | 2 | 2 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established |
| factormodels | 10 | 3 | 0 | 0 | release_templates: .github/workflows/release.yml; pypi_metadata: latest published metadata differs; requires next release; github_about: homepage |
| optimalportfolios | 47 | 1 | 5 | 0 | release_templates: .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved |
| factorlasso | 30 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| bbg-fetch | 12 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| stochvolmodels | 19 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| trendfollowing | 14 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| privateassets | 10 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| goal-based-allocation | 14 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| vanilla-option-pricers | 13 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| option-chain-analytics | 18 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |

Recorded runtime licence review: **unknown** — No runtime evidence supplied; source metadata checks do not establish a runtime licence claim.

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
