# OSS documentation standard

*Author: [Artur Sepp](https://github.com/ArturSepp)*

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

## Authorship and dates

The confirmed author for maintainer-authored documentation is
[Artur Sepp](https://github.com/ArturSepp). Place this byline immediately after the title:

~~~markdown
*Author: [Artur Sepp](https://github.com/ArturSepp)*
~~~

Preserve genuine coauthor and third-party attribution. Omit affiliations unless supplied
and confirmed for the article. Do not insert author placeholders or infer an affiliation.

When history is available, append a linked **First recorded** date:

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

## Verification and adoption

Before completing a documentation change:

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
| [FactorLasso](https://github.com/ArturSepp/factorlasso) | [AGENTS.md](https://github.com/ArturSepp/factorlasso/blob/main/AGENTS.md) | Local instructions apply. |
| [BloombergFetch](https://github.com/ArturSepp/BloombergFetch) | [AGENTS.md](https://github.com/ArturSepp/BloombergFetch/blob/main/AGENTS.md) | Local instructions apply. |
| [StochVolModels](https://github.com/ArturSepp/StochVolModels) | [AGENTS.md](https://github.com/ArturSepp/StochVolModels/blob/main/AGENTS.md) | Local instructions apply. |
| [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems) | [AGENTS.md](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/AGENTS.md) | Local instructions apply. |
| [PrivateAssets](https://github.com/ArturSepp/privateassets) | [AGENTS.md](https://github.com/ArturSepp/privateassets/blob/main/AGENTS.md) | Local instructions apply. |
| [GoalBasedAllocation](https://github.com/ArturSepp/GoalBasedAllocation) | [AGENTS.md](https://github.com/ArturSepp/GoalBasedAllocation/blob/main/AGENTS.md) | Local instructions apply. |
| [VanillaOptionPricers](https://github.com/ArturSepp/VanillaOptionPricers) | [AGENTS.md](https://github.com/ArturSepp/VanillaOptionPricers/blob/main/AGENTS.md) | Local instructions apply. |
| [OptionChainAnalytics](https://github.com/ArturSepp/OptionChainAnalytics) | [AGENTS.md](https://github.com/ArturSepp/OptionChainAnalytics/blob/main/AGENTS.md) | Local instructions apply. |
