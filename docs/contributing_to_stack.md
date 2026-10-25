---
myst:
  html_meta:
    description: >-
      Package ownership, starter tasks, setup, contribution review and verification across the OSS portfolio stack.
---

# Contributing to the OSS portfolio stack

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-10-23](https://github.com/ArturSepp/ArturSepp/commit/f650e061044695b945489d7bcd314b2b565af801)*

Maintained in [ArturSepp](https://github.com/ArturSepp/ArturSepp).
Software citation metadata belongs to each package; use its linked CITATION.cff below.

Start with one small task in an existing package contributor guide. These are proposed entry
points, not assigned issues or confirmed bugs. Recheck current source and open work before
agreeing the scope. Package contribution rules, licences and governance remain authoritative.

## Choose the owner

| Package | Owns | Starter tasks and contribution rules | Citation | Licence |
|---|---|---|---|---|
| qis | Simulation, realised holdings, performance/risk analytics and reporting | [QIS-1 to QIS-3](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CONTRIBUTING.md#starter-tasks) | [CITATION.cff](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff) | MIT |
| optimalportfolios | Allocation, constraints, rolling decisions and stack integration | [OP-1 to OP-3](https://github.com/ArturSepp/OptimalPortfolios/blob/main/CONTRIBUTING.md#starter-tasks) | [CITATION.cff](https://github.com/ArturSepp/OptimalPortfolios/blob/main/CITATION.cff) | MIT |
| factorlasso | Sparse estimation, estimator cross-validation and factor covariance | [FL-1 to FL-3](https://github.com/ArturSepp/factorlasso/blob/main/CONTRIBUTING.md#starter-tasks) | [CITATION.cff](https://github.com/ArturSepp/factorlasso/blob/main/CITATION.cff) | MIT from [1.0.4.post1](https://pypi.org/project/factorlasso/1.0.4.post1/) |

ArturSepp owns shared practices and adoption measurement. QIS does not import OP or FactorLasso;
OP consumes QIS and accepts supplied alphas and covariance. FactorModels consumes QIS and
FactorLasso; generic estimation belongs in FactorLasso. Do not copy numerical routines between
packages or introduce dependencies to complete a documentation task. Historical FactorLasso
GPL releases retain their grants; use the verified MIT release for the current factor stack.
First-party MIT does not relicense dependencies or optional backends: preserve their full
notices and the [recorded runtime qualifications](../scripts/PUBLIC_TOOLS.md#recorded-runtime-licence-review).

## Setup and a first check

Use the owning repository's CONTRIBUTING.md and AGENTS.md. Start with the existing offline
example or collected test named in the task. Record Python, package versions, extras, source
revision and the exact command. All nine tasks use public source and synthetic or packaged
fixtures; none needs vendor access, a private paper workspace or credentials.

On an ordinary checkout outside OneDrive, follow the package's existing locked development
setup, then set PowerShell `$py` to that environment's Python executable. On the maintainer's
Windows host, use these registered interpreters:

| Repository | `$py` |
|---|---|
| QuantInvestStrats | `C:\Python\QuantInvestStrats312\Scripts\python.exe` |
| OptimalPortfolios | `C:\Python\OptimalPortfolios312\Scripts\python.exe` |
| FactorLasso | `C:\Python\FactorLasso312\Scripts\python.exe` |
| ArturSepp | `C:\Python\ArturSepp312\Scripts\python.exe` |

For example, before a focused QIS check in the maintainer checkout:

```powershell
$stackRoot = Join-Path $env:USERPROFILE 'OneDrive\analytics\my_github'
Set-Location -LiteralPath (Join-Path $stackRoot 'QuantInvestStrats')
. (Join-Path $stackRoot 'ArturSepp\scripts\repo_governance\Enter-AgentRepo.ps1')
$py = 'C:\Python\QuantInvestStrats312\Scripts\python.exe'
$env:UV_PROJECT_ENVIRONMENT = 'C:\Python\QuantInvestStrats312'
& $py tools/check_docs.py --files docs/quickstart.md
```

Repeat setup after changing repositories. Never create or use a Python environment, cache,
build tree or disposable test directory under OneDrive. Use the existing governance launcher
for standard checks; its source-export profiles keep pure validation on C:. Read
[the governance workflow](../scripts/repo_governance/README.md) before choosing a source
revision. Unstaged edits are not included by the default profile. Do not stage someone else's
work to make validation see your change. For a PR candidate use `-Task docs` and record the
revision and baseline; run the owning package's additional required gates.

## Reuse the existing issue forms

Each pilot repository already has feature and bug forms under `.github/ISSUE_TEMPLATE/`.
For a starter proposal use the existing feature form's **Research or user task**, **Current
limitation**, **Proposed behavior**, **Area** and **Project boundary** fields. Add the task ID,
owner, exact source paths, reproduction steps, acceptance criteria and focused verification
command to Proposed behavior. Select the area from that repository's existing options.

Use the bug form only for observed incorrect behaviour: include version, Python/OS, a minimal
public reproducer, expected versus observed results and the full failure. Keep required form
fields and boundary checkboxes. Draft issue text locally first; a local task description is
not a published issue or an instruction to contact anyone.

## Review, attribution and automation-assisted changes

- Keep one topic per PR and identify the owner and starter-task ID. Describe the original
  limitation, final change, exact checks and any skipped or pending verification. A maintainer
  decides scope and labels; numerical changes require domain review and independent references.
- For a bug fix, show the relevant regression failing before the fix and passing after it.
  For new validation, demonstrate that the check rejects a controlled failure in disposable
  source, restore it, then run the real case. Do not change seeds or expected results merely
  to obtain a pass. Documentation-only additions need source checks and a render review;
  passing tests alone do not prove that prose is understandable.
- Use the existing canonical examples, test fixtures, notebooks and documentation tooling.
  Keep public signatures, defaults and dependencies stable. Record the installed version and
  actual imported module path when an integration result depends on the environment. A skip
  for a missing optional dependency does not establish that integration works.
- Automation can help draft code and prose. The submitting contributor is responsible for
  understanding the diff, verifying symbols against current source, running checks, checking
  references and licensing, and disclosing material assistance and remaining limitations in
  the PR. Do not submit a stream of unreviewed generated changes. Maintainers may request a
  smaller diff, clearer evidence or a manual explanation before acceptance.
- Preserve third-party attribution and comply with the owning package's licence. Credit
  actual contributors in the PR and any agreed acknowledgement; do not invent coauthors or
  affiliations. Authorship metadata and paper citations follow the
  [documentation standard](documentation_standard.md). Release attribution follows the
  package maintainer's release process; a contribution does not require a version bump.

Support follows each package's existing governance and contribution guidance. There is no
promised review response time. No task includes publication, outreach or assignment to a
named person.

## Independent reader check and later measurement

One reader other than the implementation author should select a task, record their setup,
follow its reproduction and run its focused check without coaching. Record success or failure
for setup, reproduction and verification separately, including exact commands, revision,
versions, output and any confusing step. A reader can evaluate the starter instructions
without implementing the proposed change. Record their result and resolve blocking defects
before describing onboarding as human-verified. An automated dry run is separate evidence.

At later adoption checkpoints, use the existing adoption dashboard where available and GitHub review records. Count distinct external contributors with accepted work and repeat external
contributors in the stated period; name the denominator, period and identity treatment.
Distinguish accepted docs/tests/code from raw commits, generated PRs, bots and maintainer
activity. Do not infer contributor retention from downloads, stars or raw commit volume.

## Additional package entry points

The original nine QIS/OP/FactorLasso proposals above remain the Q3 pilot. Six additional
package guides add three bounded proposals each, using their existing issue forms and
contribution rules. All 18 are proposals, not assigned issues or confirmed bugs. PrivateAssets
links to its contribution scope and review requirements. Human
verification of the original Q1 and Q3 pilots remains pending; automated checks and local
render inspection do not establish newcomer success.

| Owner | Owns / first task | Starter proposals | Licence | Citation |
|---|---|---|---|---|
| [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) | Price vanilla options and invert implied volatility | [VOP-1 to VOP-3](https://github.com/ArturSepp/VanillaOptionPricers/blob/main/CONTRIBUTING.md#starter-tasks) | MIT | [CITATION.cff](https://github.com/ArturSepp/VanillaOptionPricers/blob/main/CITATION.cff) |
| [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) | Compare closed-form trend-following risk/return | [TF-1 to TF-3](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CONTRIBUTING.md#starter-tasks) | MIT from [1.3.1.post1](https://pypi.org/project/trendfollowing/1.3.1.post1/) | [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff) |
| [PrivateAssets](https://github.com/ArturSepp/PrivateAssets) | Evaluate cashflows with public-market equivalents | [Contribution scope](https://github.com/ArturSepp/PrivateAssets/blob/main/CONTRIBUTING.md#scope) | MIT | [CITATION.cff](https://github.com/ArturSepp/PrivateAssets/blob/main/CITATION.cff) |
| [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) | Explore a goal-based allocation under regime switching | [GBA-1 to GBA-3](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/CONTRIBUTING.md#starter-tasks) | MIT | [CITATION.cff](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/CITATION.cff) |
| [StochVolModels](https://github.com/ArturSepp/StochVolModels) | Price a fixed LogSV model | [SVM-1 to SVM-3](https://github.com/ArturSepp/StochVolModels/blob/main/CONTRIBUTING.md#starter-tasks) | MIT | [CITATION.cff](https://github.com/ArturSepp/StochVolModels/blob/main/CITATION.cff) |
| [OptionChainAnalytics](https://github.com/ArturSepp/OptionChainAnalytics) | Reconstruct and query a synthetic option chain | [OCA-1 to OCA-3](https://github.com/ArturSepp/OptionChainAnalytics/blob/main/CONTRIBUTING.md#starter-tasks) | MIT | [CITATION.cff](https://github.com/ArturSepp/OptionChainAnalytics/blob/main/CITATION.cff) |
| [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) | Check installation and synthetic response-shaped inputs | [BBG-1 to BBG-3](https://github.com/ArturSepp/BloombergFetch/blob/main/CONTRIBUTING.md#starter-tasks) | MIT | [CITATION.cff](https://github.com/ArturSepp/BloombergFetch/blob/main/CITATION.cff) |

Use each guide's actual Area choice and boundary checkboxes; field labels vary by package.
For the maintainer checkout, replace `$py` with the corresponding external
`C:\Python\<Repository>312\Scripts\python.exe` and rerun `Enter-AgentRepo.ps1` after
changing owner. Keep generated state on C. Task scope stays in documentation; numerical
implementations, seeds, fixtures, signatures and dependencies require a separately agreed task.
BloombergFetch's synthetic check still requires the real `blpapi` SDK and cannot establish
connectivity, entitlement or licensed-data correctness. Do not attach vendor responses.
