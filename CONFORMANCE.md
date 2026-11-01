# Public package conformance

Observed: 2026-11-01T06:52:24.079423+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 37 | 2 | 2 | 1 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established; github: HTTP Error 403: rate limit exceeded |
| factormodels | 9 | 2 | 0 | 1 | release_templates: .github/workflows/release.yml; pypi_metadata: latest published metadata differs; requires next release; github: HTTP Error 403: rate limit exceeded |
| optimalportfolios | 45 | 1 | 5 | 1 | release_templates: .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved; github: HTTP Error 403: rate limit exceeded |
| factorlasso | 29 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| bbg-fetch | 11 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| stochvolmodels | 18 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| trendfollowing | 13 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| privateassets | 9 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| goal-based-allocation | 13 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| vanilla-option-pricers | 12 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |
| option-chain-analytics | 17 | 2 | 0 | 0 | dependency_graph: missing import bans: factormodels; release_templates: .github/workflows/release.yml |

Recorded runtime licence review: **unknown** — No runtime evidence supplied; source metadata checks do not establish a runtime licence claim.

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
