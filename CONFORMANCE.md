# Public package conformance

Observed: 2026-10-17T09:22:08.530657+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 35 | 1 | 2 | 1 | release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established; github: HTTP Error 403: rate limit exceeded |
| optimalportfolios | 36 | 1 | 5 | 1 | release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved; github: HTTP Error 403: rate limit exceeded |
| factorlasso | 25 | 1 | 0 | 1 | release_templates: .github/workflows/release.yml; github: HTTP Error 403: rate limit exceeded |
| bbg-fetch | 10 | 1 | 0 | 1 | release_templates: .github/workflows/release.yml; github: HTTP Error 403: rate limit exceeded |
| stochvolmodels | 16 | 1 | 0 | 1 | release_templates: .github/workflows/release.yml; github: HTTP Error 403: rate limit exceeded |
| trendfollowing | 12 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| privateassets | 10 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| goal-based-allocation | 12 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| vanilla-option-pricers | 12 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |
| option-chain-analytics | 16 | 1 | 0 | 0 | release_templates: .github/workflows/release.yml |

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
