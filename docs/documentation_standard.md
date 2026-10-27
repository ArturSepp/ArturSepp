# OSS documentation standard

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-09-20](https://github.com/ArturSepp/ArturSepp/commit/59afe221758e9b7e5c7bcdd5ddd012b6ddd14d1f)*

Maintained in [the ArturSepp OSS stack](https://github.com/ArturSepp/ArturSepp).

This is the common authoring standard for the public Python packages maintained in
[ArturSepp's OSS stack](https://github.com/ArturSepp). It covers methodology articles,
analytics explanations, README guides, tutorials, and other human-authored documentation.
Use it for new pages and substantive revisions; adding a link to this guide does not certify
that an existing documentation tree has completed migration or review.

Start with the [article template](#copyable-methodology-template), then read the owning
repository's instructions in the [package directory](#package-directory). Common authoring
rules live here. Package supplements own their API contracts, data policies, analytics
commands, supported build configuration, and verification procedures.

## Scope and ownership

Write in a neutral, encyclopedic style: define the concept before its implementation,
explain the assumptions, show a small example, and cite substantive claims. Distinguish a
published method from an implementation choice or an experimental result. Expand acronyms
at first use and explain what each figure establishes.

Each package's AGENTS.md links here. Keep general rules in this document and link to them
from local supplements instead of copying the template. Explicit local exceptions apply
only to the named package or format. Record and reconcile conflicting instructions; do not
silently apply one package's conventions across the stack.

Preserve repository-specific docstring styles, RST API sources, paper formats, and canonical
documentation locations. The Markdown article template does not prescribe Python docstring
syntax. Generated API pages and mirrored sources are edited through their producer.
Machine-readable records, licences, changelogs, and agent instructions retain their own
formats. Agent plans, audits, and execution records belong in the repository's ignored
root agents/ directory, as its AGENTS.md requires.

## Article structure

A methodology article has one H1 title, a linked author byline, visible software links,
and a short definition-led introduction. Use these H2 sections in order, with descriptive
H3 subsections as needed:

| Section | Content |
|---|---|
| Overview | The question answered, scope, and suitable uses. |
| Inputs, notation, and assumptions | Symbols, dimensions, units, frequencies, timing, and data policies. |
| Methodology | Definitions and equations with their interpretation. |
| Worked example | Fixed inputs, a small result, and what it demonstrates. |
| Implementation in PACKAGE | Verified public entry points, input/output contract, canonical runnable source, and reproduction context. |
| Interpretation and limitations | Assumptions, uncertainty, numerical qualifications, edge cases, and unsuitable uses. |
| See also | A short selection of relevant methods and guides. |
| References | Verified primary method sources and software citation metadata. |

Replace PACKAGE with the import name used by the owning repository's article convention.
QIS uses "Implementation in qis"; OP uses "Implementation in optimalportfolios".

Installation, quickstart, navigation, gallery, architecture, comparison, and contributor
pages use a shorter utility form: one H1, byline, software links, a useful lead, and logical
headings. Do not add empty methodology sections to these pages.

## Required attribution links

Every human-authored package page **must** place one attribution block immediately after its
title, with these four ordinary links:

| Link | Required target |
|---|---|
| Author | [Artur Sepp](https://github.com/ArturSepp), preserving genuine coauthors and third-party credits. |
| Repository | The page's owning software repository, using its canonical GitHub URL. |
| Software citation | That repository's `blob/main/CITATION.cff`, with the visible label `CITATION.cff`. |
| First recorded | The earliest verified source commit, with its committer calendar date as the label and its full 40-character SHA in the URL. |

For an article with verified history, use this Markdown layout, replacing every example token:

~~~markdown
*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [YYYY-MM-DD](https://github.com/ArturSepp/REPOSITORY/commit/FULL_COMMIT_SHA)*

Implemented in [PACKAGE](https://github.com/ArturSepp/REPOSITORY).
Software citation: [CITATION.cff](https://github.com/ArturSepp/REPOSITORY/blob/main/CITATION.cff).
~~~

Use native RST links for retained RST pages. The owning package may use its established display
name; upstream handoff pages may say `Documented in PACKAGE` while naming the actual upstream
implementation. Repository and citation links always identify the current owning package.

This requirement covers methodology and utility pages, root and packaged READMEs, contributor
and example guides, governance and community policies, and maintained redirect pages. Preserve
the formats of licences, legal notices, manuscripts, agent instructions, submission templates,
machine-readable records and generated API stubs; change generated attribution through its
producer. Shared profile/governance guides are not software packages: link their source
repository and the applicable package citations or package directory, without inventing a
profile-repository `CITATION.cff`.

A new uncommitted page has the linked author, repository and citation block, with **First
recorded pending** in the working audit until a real commit exists. Missing or shallow history
is an evidence limitation to resolve or record, not permission to invent a date. A page with
available commit history must not retain an author-only byline.

If an article moved between public repositories, its First recorded link may identify the
verified earlier source repository. Explain that transfer beside the header and retain the
real source URL; do not attach the former date or SHA to the new repository's URL. Follow the
history checks below and record the verified original path in the audit.

## Authorship and dates

The confirmed author for maintainer-authored documentation is
[Artur Sepp](https://github.com/ArturSepp). Place this byline immediately after the title:

~~~markdown
*Author: [Artur Sepp](https://github.com/ArturSepp)*
~~~

Preserve genuine coauthor and third-party attribution. Omit affiliations unless supplied
and confirmed for the article. Do not insert author placeholders or infer an affiliation.

Every page already recorded in available commit history must append a linked **First recorded** date:

~~~markdown
*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [YYYY-MM-DD](https://github.com/ArturSepp/REPOSITORY/commit/FULL_COMMIT_SHA)*
~~~

Replace the date, repository, and full 40-character commit hash with verified evidence.
Use the earliest available commit recording the article, following renames and earlier
sources such as RST. Inspect the history, rather than using a file modification time:

~~~console
git log --follow --format="%H %cI" -- docs/ARTICLE.md
~~~

Inspect former source paths as well, and choose the earliest evidenced committer date,
preserving that timestamp's calendar date. Confirm that the linked commit contains the
relevant source. A Markdown conversion or move does not restart the article's history.
If history is shallow or incomplete, record that limitation in the working audit.

This date records repository inclusion; it is not proof of the exact GitHub push time,
public posting, original research date, or peer review. A new uncommitted page keeps the
author-only byline until a commit exists. Do not use the date of this edit or a release as
a substitute. Keep substantive review dates, data cutoffs, and image generation timestamps
separate; a rebuild does not establish a new methodological review.

## Copyable methodology template

Replace topic and package tokens before publication. The byline is ready to use for a
new page; add First recorded only when commit evidence exists. For MyST/Sphinx pages,
retain the description front matter below. Other formats use their native metadata.

~~~~markdown
---
myst:
  html_meta:
    description: >-
      A factual description of TOPIC and its PACKAGE implementation.
---

# TOPIC

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [PACKAGE](https://github.com/ArturSepp/REPOSITORY).
Software citation: [CITATION.cff](https://github.com/ArturSepp/REPOSITORY/blob/main/CITATION.cff).

Define the concept and its scope in a short lead.

## Overview

Explain the question and when this method is useful.

## Inputs, notation, and assumptions

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| INPUT | Definition | Units, dimensions, frequency, and timing |

## Methodology

Introduce each equation, define its symbols, and interpret the result.

## Worked example

Give fixed inputs, a small computed result, and its interpretation.
Label synthetic data explicitly.

## Implementation in PACKAGE

Link to verified public entry points and the canonical runnable example.
State required extras, the reproduction command, and actual source/version context.
Record execution or review dates only for checks performed.

## Interpretation and limitations

Explain assumptions, uncertainty, numerical qualifications, and edge cases.

## See also

Link to relevant methods and guides.

## References

- Verified author, year, title, venue, and DOI or primary-source link.
- [PACKAGE software citation](https://github.com/ArturSepp/REPOSITORY/blob/main/CITATION.cff).
~~~~

## Portable mathematics

For Markdown articles, use single-dollar inline math and standalone double-dollar
display delimiters, with blank lines around each display block. GitHub and VS Code
support dollar-delimited math; MyST requires its dollarmath extension. See the
[GitHub syntax](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions),
[MyST configuration](https://myst-parser.readthedocs.io/en/latest/syntax/math.html), and
[VS Code preview documentation](https://code.visualstudio.com/docs/languages/markdown#_math-formula-rendering).

~~~markdown
Let $x_i$ be observation $i$ in a sample of $n$ observations.

$$
\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i.
$$
~~~

- Keep semantic equations out of code spans and fences; fences above demonstrate source.
  Do not use MyST-only math directives or equation roles in portable Markdown prose.
- Use basic TeX commands. Put aligned, cases, or matrix environments inside display blocks.
  Break long expressions at meaningful equalities and avoid custom macros.
- Define symbols before use, use explicit timing subscripts, and keep one meaning per symbol.
  Keep complex formulas out of table cells; use `\lvert` and `\rvert` for absolute-value bars
  where raw pipes would conflict with table syntax.
- Prefer links to derivation headings over renderer-specific equation numbering.
  State currency as USD 100 near math to avoid ambiguous dollar delimiters.
- Repair formatting without changing mathematical meaning, units, or numerical results.

Retained RST pages use native RST math syntax and their existing Sphinx configuration;
do not paste Markdown delimiters into RST. Basic CommonMark viewers may display TeX source,
so provide access to the rendered site. Inspect GitHub Markdown, Sphinx, and VS Code
independently where supported; one successful renderer does not certify the others.

## References and executable examples

Every human-authored article or utility page links to its owning software repository
and canonical CITATION.cff using ordinary links. Cite additional packages where their
calculations are used. In particular, identify
[qis](https://github.com/ArturSepp/QuantInvestStrats) and its
[citation metadata](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff)
when it supplies analytics or reporting. A stack reference does not add a runtime dependency
to a standalone package.

Cite methodological claims near the claim and give bibliographic details under References.
Check names, dates, titles, equation numbers, and DOIs against primary sources. Follow each
repository's rules for published-paper versus source numbering. Software citations identify
implementations; they do not replace the source of a method.

Verify public names, signatures, enum members, input shapes, and units before writing an
example. Use the owning package's declared export contract. Keep numerical implementations
in their canonical modules and respect the stack's dependency direction. Preserve each
repository's docstring convention and executable README, doctest, and notebook contracts.

Link to one canonical runnable script rather than maintaining copied full scripts. Provide
ordinary source links beside Sphinx includes and generated API references. A self-contained
example supplies its inputs and dependencies; label fragments and optional services clearly.
Use deterministic synthetic inputs for unattended teaching examples. Where vendor access is
the subject, state its prerequisites and provide an offline explanation without distributing
licensed data. A fixed historical end date does not freeze a provider's adjusted history.

State relevant return conventions, annualisation, estimation and reporting frequencies,
warmup, missing-data policies, and decision versus implementation timing. For optimisation,
explain constraints, tolerances, accepted solver statuses, and fallbacks. For option analytics,
state timezones, maturity units, price/volatility quotation, and discount conventions.

## Figures and analytical provenance

Every displayed analytics image needs a registered producer and a documented batch command
that regenerates the complete package bundle. Extend existing analytics tooling or paper
orchestrators; do not create a second implementation solely for a documentation chart.

The registry and result record identify the consuming page, output path, producer, inputs
or configuration, sample, seed where applicable, conventions, actual software source, and
generation timestamp. Include supporting numerical results and hashes sufficient to connect
the figure, table, and caption to the same calculation. Record dirty source identity when a
clean commit does not identify the code that ran.

Keep fixed synthetic fixtures and teaching seeds fixed. Label synthetic exhibits and
historical evidence clearly. Separate data cutoff, generation, and visual review dates.
A changed timestamp alone does not make an old empirical analysis current.

Captions explain the question and result; alt text describes the comparison. Check axes,
units, legends, readable labels, clipping, colour consistency, and light/dark contrast at
normal page width. Provide a larger view or supporting table when the preview is insufficient.

Generate into a fresh directory outside the source checkout using its prescribed environment
and output policy. Validate the complete bundle and review the images before replacing
previews. A registry entry or successful script run alone is not visual approval. Commit
only deliverables expressly permitted by the owning repository; this guide does not extend
QIS/OP's preview allowlist to packages that prohibit generated figures.

For legacy images without recoverable provenance, record the gap in the package inventory.
Do not claim reproducibility until the producer and inputs exist and have been checked.

## Navigation and discoverability

Use descriptive titles, stable page basenames, and concise search descriptions. Link each
new page from the documentation index and a relevant neighbouring guide. Preserve old anchors
or provide redirects when moving content. Keep ordinary links useful in the source viewer
as well as in the rendered site.

README pages should offer a clear purpose, installation, a working first example, a route to
methodology and API documentation, and citation guidance. Link related stack packages where
the connection helps the reader choose the right tool. Support comparison and performance
claims with reproducible evidence; distinguish experimental features from supported APIs.

Use the existing site configuration for metadata and navigation. Publicity does not justify
unverified superiority claims, fabricated adoption statistics, or duplicate method pages.


The generated sitemap must contain only preferred, indexable URLs, and each entry must match
one absolute canonical link in the rendered target page. When the homepage canonical uses the
version root, list that root instead of its `index.html` alias. Exclude redirects, `noindex`
pages and search/index helper pages. Preserve each package's declared channel policy; a newer
development page must not point to a missing released-page counterpart. See
[Google's canonical URL guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).

Verify the actual HTML and XML together after a strict build, including stable, latest and
numbered-channel fixtures and an incremental build. Keep the sitemap producer inside the
owning repository, use the existing documentation toolchain, and record hosted checks separately
from local verification. A corrected source needs publication and a search-engine recrawl;
a historical alternate-page report does not by itself establish a new defect.

### Independent HTTP verification of published sitemaps

Use [the shared HTTP verifier](../scripts/verify_sitemaps.py) after the intended source
revision has built successfully on Read the Docs. Fetch the exact plain root `/sitemap.xml`
and the intended default/indexed version's `/en/<version>/sitemap.xml` through an independent
HTTP client. A browser view, reload or browser-derived response alone must never establish
that a deployment is stale. Do not substitute a cache-busting query URL for the plain URL.

```console
python scripts/verify_sitemaps.py --site https://bloombergfetch.readthedocs.io --version latest --check-pages
```

Run this command from the shared ArturSepp repository with its prescribed external interpreter
and generated-state setup. Repeat `--site` for sites sharing the same intended channel. QIS
uses `--version stable`; preserve every package's existing policy. Use `--output` to retain
JSON evidence outside the checkout, and optionally `--expected-sitemap` with one site to compare
the served inventory against the actual local build. See the [tool guide](../scripts/PUBLIC_TOOLS.md#live-sitemap-verification).

Record request URLs, UTC check time, HTTP status, selected cache/routing headers and body
SHA-256 digests. Inspect `Cache-Control`, `Age`, `ETag`, `Last-Modified`, `CF-Cache-Status`,
`CF-Ray` and available equivalent/routing headers. `HIT`, a large age, or a different ETag
alone does not prove stale content. Compare the complete parsed URL inventories; equivalent
XML with different ordering, whitespace or hashes still agrees. Keep those byte differences
as diagnostics. Verify listed pages' single matching canonical and absence of meta/HTTP
`noindex` or refresh redirects. Normalize only the homepage alias, never nested `api/index.html`.

Report an independent HTTP inventory disagreement as an **observed mismatch**, with its
response evidence. It does not by itself prove which cache or origin is stale. Compare the
intended project/default version, deployed build and source inventory before changing hosting
settings or triggering more builds. A diagnostic revalidation request may supplement the
plain response; record its headers and do not replace the plain-URL result with it.

HTTP 403/429, security challenges, transport failures and incomplete page checks are
**unverified**, never a pass or proof of stale deployment. Stop requests on 429, respect
`Retry-After`, and do not evade challenges. Live consistency checks establish the observed
served content, not every CDN edge, the deployed source commit or Google's eventual indexing.
The verifier is an explicit online maintainer check; CI exercises deterministic offline fixtures.

Read the Docs serves a custom sitemap from the project's default version when available;
otherwise it generates a version list. See [its sitemap behavior](https://docs.readthedocs.com/platform/stable/reference/sitemaps.html)
and [CDN refresh rules](https://docs.readthedocs.com/platform/stable/reference/cdn.html).
Platform cache refresh and a client/intermediary cache expiring are distinct observations.

### Historical URLs and retired API documentation

A healthy current sitemap does not cover pages removed from it. Before renaming a page,
removing an API stub or transferring a capability, review public Git history, prior
published links and the source that generated the old API inventory. Include RST/Markdown
renames, autosummary lists and generated export/ownership records. Do not execute historical
package code merely to enumerate URLs. Record the source commit and path, and distinguish
an evidenced article or API entry point from a guessed internal build path.

Check candidate URLs with independent HTTP requests under the package's actual indexed
channel. Missing internal includes, non-documentable module/data exports and unpublished
work do not automatically need redirects. A public compiled function may instead link to
the handbook section that documents its exact contract. A removed API must not be described
as restored merely because its old documentation URL now resolves.

Keep reviewed mappings in the owning repository's `tools/docs_redirects.json`. Use enabled,
non-forced Read the Docs Page Redirects with explicit HTTP 301 and an absolute HTTPS target.
Choose the current owning package's relevant API, migration note or handbook section; verify
the actual destination fragment. Existing archive pages take precedence. Do not redirect
unrelated removals to the homepage or add redirect sources to the canonical sitemap.

Validate local destination files and anchors during successful HTML builds, and preserve
reviewed sources with regression tests. After publication, use the shared HTTP verifier's
`--redirect-manifest` option to check exact Locations, destination HTTP 200, self-canonical
and indexability metadata, and anchors. Verify both active `latest` and `stable` legacy paths.
For a non-default channel, evaluate the redirect subreport separately: its sitemap normally
differs from the domain root's indexed channel. Preserve request pacing and throttle evidence;
requests to a common API host share one rate budget even when package sites differ.
See the [redirect verification guide](../scripts/PUBLIC_TOOLS.md#historical-urls-and-permanent-redirects)
and [Read the Docs redirect behavior](https://docs.readthedocs.com/platform/stable/user-defined-redirects.html).

### Automated historical URL monitoring

Run live URL monitoring separately from normal commits and required CI. Temporary access,
network or hosting failures are unverified operational observations, not source-code failures.
Required checks exercise offline fixtures; do not add an online availability gate to push,
pull-request or pre-commit checks. The shared monitor learns published sitemap URLs, retains
removed URLs, and checks reviewed published redirects on the correct documentation channels.
Run the shared monitor from a separate scheduled GitHub Actions workflow so it does not
depend on a maintainer computer. Persist its URL history, confirmation state and pending
notifications on the dedicated automation state branch, separate from normal source commits;
expiring artifacts or evictable caches must not be the only copy. Local diagnostic state
remains outside OneDrive on the maintainer host.

Confirm a new broken URL or metadata defect on two definitive observations at least one hour
apart. Suppress repeated alerts for unchanged issues, report verified recoveries once, and
report sustained inability to monitor separately from a broken-site finding. An unverified
observation cannot confirm a pending failure or clear an active one. Preserve independent
HTTP evidence, host pacing, the global throttle stop and optional-source semantics. Review
channel-policy changes explicitly rather than silently changing QIS from stable to latest.
Use a tracking issue assigned to the maintainer for new confirmed failures and recoveries;
store pending delivery before posting, and deduplicate retries with persistent event markers.
Isolate the writer's contents/issue permissions from the checking job, serialize runs, and
never expose write credentials to pull-request code or execute downloaded documentation.
See the [scheduled monitor guide](../scripts/PUBLIC_TOOLS.md#scheduled-documentation-monitor)
for the command, coverage limits, persisted state and notification contract.

## Verification and adoption

Before completing a documentation change:

Verify the four attribution links on every revised human-authored page. Check that the author
link is correct, the repository and `CITATION.cff` identify the owning package, and the recorded
date, full commit SHA and source path agree with Git history. Report uncommitted pages as
pending evidence rather than claiming every date is verified.

1. Run the owning repository's source checks and applicable example/doc tests. Register new
   pages and images in its existing inventories; keep migration and review status explicit.
2. Build changed site sources with the established strict Sphinx configuration and check local
   links and anchors. Check external links separately and record unavailable targets honestly.
3. Verify changed calculations against an independent reference where applicable. Do not
   regenerate numerical baselines merely to make a formatting change pass.
4. Inspect affected math and figures in the supported viewers. Record exactly what was checked,
   with the command, source context, result, and any pending review in the local working audit.

The repository's AGENTS.md supplies interpreter and generated-state requirements. On the
maintainer's Windows/OneDrive checkouts, use the prescribed external environment and C-local
source export for builds: some builders write generated sources beside their inputs.
Do not copy a CI command that would create a OneDrive-local environment or cache.

Source checks, numerical checks, rendering review, and hosted publication are different
outcomes. A source pass does not mark a pending article reviewed. Adding this standard
introduces no automatic publication, fixture refresh, or blanket claim of stack compliance.

## Package directory

Package identity and dependency ownership are recorded in the
[public registry](../scripts/public_registry.json). Follow the linked local instructions
for build commands, docstring conventions, and numerical contracts.

| Package repository | Local instructions | Documentation supplement |
|---|---|---|
| [QuantInvestStrats (qis)](https://github.com/ArturSepp/QuantInvestStrats) | [AGENTS.md](https://github.com/ArturSepp/QuantInvestStrats/blob/main/AGENTS.md) | [QIS supplement](https://github.com/ArturSepp/QuantInvestStrats/blob/main/docs/documentation_standard.md) |
| [OptimalPortfolios](https://github.com/ArturSepp/OptimalPortfolios) | [AGENTS.md](https://github.com/ArturSepp/OptimalPortfolios/blob/main/AGENTS.md) | [OP supplement](https://github.com/ArturSepp/OptimalPortfolios/blob/main/docs/documentation_standard.md) |
| [FactorLasso](https://github.com/ArturSepp/factorlasso) | [AGENTS.md](https://github.com/ArturSepp/factorlasso/blob/main/AGENTS.md) | [FactorLasso supplement](https://github.com/ArturSepp/factorlasso/blob/main/docs/documentation_standard.md) |
| [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) | [AGENTS.md](https://github.com/ArturSepp/BloombergFetch/blob/main/AGENTS.md) | Local instructions apply. |
| [StochVolModels](https://github.com/ArturSepp/StochVolModels) | [AGENTS.md](https://github.com/ArturSepp/StochVolModels/blob/main/AGENTS.md) | [Documentation supplement](https://github.com/ArturSepp/StochVolModels/blob/main/docs/documentation_standard.md) |
| [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) | [AGENTS.md](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/AGENTS.md) | [Documentation supplement](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/docs/documentation_standard.md) |
| [PrivateAssets](https://github.com/ArturSepp/privateassets) | [AGENTS.md](https://github.com/ArturSepp/privateassets/blob/main/AGENTS.md) | Local instructions apply. |
| [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) | [AGENTS.md](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/AGENTS.md) | [Documentation supplement](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/docs/documentation_standard.md) |
| [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) | [AGENTS.md](https://github.com/ArturSepp/VanillaOptionPricers/blob/main/AGENTS.md) | Local instructions apply. |
| [OptionChainAnalytics](https://github.com/ArturSepp/OptionChainAnalytics) | [AGENTS.md](https://github.com/ArturSepp/OptionChainAnalytics/blob/main/AGENTS.md) | Local instructions apply. |
| [FactorModels](https://github.com/ArturSepp/FactorModels) | [AGENTS.md](https://github.com/ArturSepp/FactorModels/blob/main/AGENTS.md) | Local instructions apply. |

## Release channels and generated navigation

Package documentation distinguishes released `stable` builds from development `latest` builds.
Show the actual build version and link to channel home pages: a page or symbol added on main
may be absent from the release. Preserve each build's own canonical URL. A stable alias can lag
PyPI; it is not evidence of the newest published version. If released HTML is unavailable,
link a verified tagged-source guide and explain the fallback instead of inventing an alias.

State a minimum supported released version beside public examples or in their linked catalogue.
A conservatively verified support floor is not a historical first-introduction claim. Mark any
source-only capability explicitly, without marking already released neighbouring features as
unreleased. Explain the owning package's actual compatibility policy and source/dependency
licences; changing a classifier or source licence is separate work.

Where a package uses Sphinx, generate `llms.txt` and an API companion at successful HTML build
time through its existing indexing extension. Discover pages from Sphinx and exports from the
same verified contract as the API producer (`__all__` or the owning documentation inventory).
Use Sphinx's real object targets; omit invented anchors and fail on nonexistent declared exports.
Keep output deterministic and out of the source tree. Verification includes source checks,
strict docs/CI profiles, local targets and anchors, channel navigation, and Markdown/HTML review.
