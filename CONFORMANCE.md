# Public package conformance

Observed: 2026-10-19T10:47:34.095406+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 36 | 1 | 2 | 0 | release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established |
| optimalportfolios | 38 | 1 | 5 | 0 | release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved |
| factorlasso | 27 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| bbg-fetch | 11 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| stochvolmodels | 17 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| trendfollowing | 13 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| privateassets | 10 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| goal-based-allocation | 12 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| vanilla-option-pricers | 12 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| option-chain-analytics | 16 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
