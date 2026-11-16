# Governance

ChemAgent Index is a research infrastructure preview. Its maintainers have not yet established an independent scientific advisory board or completed external benchmark review. The following policies define the intended release process, not a claim of existing certification.

## Scientific control

Benchmark editors propose tasks and document provenance, licensing, ambiguity, expected outputs and scientific limitations. Independent chemistry reviewers must approve scientific correctness before a benchmark is represented as externally validated. Expert tasks require rubrics and multiple blinded reviewers; that workflow is not implemented in v0.2.0.

## Methodology changes

Use semantic versions for software, benchmarks and scoring profiles. Changes that invalidate score comparability require a new major benchmark/profile version. Additive coverage can be minor only when comparisons are explicitly scoped to the same task set. Corrections receive a new version and changelog; already published runs are retained and may be flagged rather than rewritten. Content hashes guard against accidental version reuse.

## Conflict management

Developers' own agents receive no preferential treatment. Authors disclose ownership, employment, funding and financial interests. Reviewers recuse themselves from affected scoring decisions. Sponsor funding, commercial subscriptions or donations must not influence weights, inclusion, exclusion or rankings. Material sponsorship must be visibly disclosed.

## Submissions and disputes

A future submission moves through draft, submitted, under_review, approved or rejected. The preview implements only optional intake storage and submitted status. Before evaluation, reviewers must verify access, version identity, licensing, permitted tools and provenance. Rejection reasons and appeals should be recorded. Never present submitted scores as independently verified before rerunning the evaluation.

## Hidden sets and publication

Private tasks stay outside public repositories and APIs. Publish construction methodology and distribution summaries without exposing test answers. Rotate compromised sets under new versions. Public development tasks are explicitly contaminated and unsuitable as sole evidence for broad rankings. Publish intervals and all relevant submetrics; ordering alone never establishes superiority.
