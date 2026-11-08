# Public package conformance

Observed: 2026-11-08T11:56:36.239494+00:00 · mode: online

GitHub Release pages are optional. Unpublished source versions are preparation states.

| Package | Pass | Fail | Known gap | Unknown | Findings |
|---|---:|---:|---:|---:|---|
| qis | 42 | 3 | 2 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 5.15.0: Multiple matching packaged-source commits; release commit not uniquely established; historical_provenance: 5.18.0: Multiple matching packaged-source commits; release commit not uniquely established; github: HTTP Error 503: Service Unavailable |
| factormodels | 9 | 3 | 0 | 1 | action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; pypi_metadata: latest published metadata differs; requires next release; github: HTTP Error 503: Service Unavailable |
| optimalportfolios | 46 | 2 | 5 | 1 | action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml, .github/scripts/release_guard.py; historical_provenance: 6.21.1: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.2: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.3: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 6.21.4: Published settings.yaml differs from all checked repository candidates; provenance unresolved; historical_provenance: 7.1.0: Published settings.yaml differs from all checked repository candidates; provenance unresolved; github: HTTP Error 503: Service Unavailable |
| factorlasso | 30 | 2 | 0 | 1 | action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| bbg-fetch | 10 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| stochvolmodels | 17 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| trendfollowing | 12 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| privateassets | 8 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| goal-based-allocation | 12 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| vanilla-option-pricers | 11 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |
| option-chain-analytics | 17 | 3 | 0 | 1 | dependency_graph: missing import bans: factormodels; action_pins: dependabot-merge.yml: mutable action read; release_templates: .github/workflows/release.yml; github: HTTP Error 503: Service Unavailable |

Recorded runtime licence review: **unknown** — No runtime evidence supplied; source metadata checks do not establish a runtime licence claim.

This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.
