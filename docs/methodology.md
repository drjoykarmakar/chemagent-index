# ChemAgent Index: methods for auditable evaluation of AI systems in chemistry

**Software version:** 0.2.0
**Scoring version:** 0.1.0
**Benchmark:** ChemAgentBench public development set v0.1.0
**Status:** implementation methods draft; not peer-reviewed and not a scientific validation study

## Abstract

ChemAgent Index provides a reproducible framework for chemistry-specific evaluation of AI models and agents. The architecture separates task definitions, provider requests, chemical validation, scoring, statistical analysis, storage and public presentation. The implementation comprises 60 original synthetic development tasks, digest-pinned local model inference, three separately labeled deterministic mock systems, RDKit validation, structured field rubrics, experimental reliability and reproducibility measures, and category-stratified cluster-bootstrap uncertainty. The release demonstrates functioning evaluation infrastructure. Individual runs report observed performance on the development collection. They do not establish clinical utility, chemical safety or external benchmark validity.

## Motivation

A fluent answer can contain an invalid molecule, incorrect unit conversion or unsupported evidence claim. Evaluation must therefore separate persuasive language from checkable scientific content. General-purpose scores do not, by themselves, establish chemistry competence. ChemAgent Index exposes both the scoring process and its evidential limits, while preserving configuration and version identity for later replication.

The intended unit of comparison is a fully specified system: model revision, agent implementation, tool access, prompt configuration, benchmark version and scoring policy. A foundation model with no tools is not interchangeable with an agent that uses chemical databases and code execution.

## Benchmark design

The public development benchmark consists of six categories with ten tasks each. Items are authored synthetic fixtures, not observations from published experiments. Tasks are introductory or intermediate; none is claimed to be expert-level. Every item records provenance, license, curation method, review status, contamination risk, ambiguity, expected schema, answer and rubric. No external references are fabricated.

Numerical variants and related exercises share template cluster identifiers. This acknowledges that closely related tasks are correlated. Public task bytes are hashed, and the manifest records the exact count and checksum. Loader checks detect duplicate task identifiers and duplicate prompt/input pairs. Reference correctness is checked with arithmetic and independent RDKit calculations in tests. These checks are necessary but do not replace external expert scientific review.

## Task categories

Chemistry reasoning measures calculations involving dilution, molarity, yields, idealized pH, equilibrium ratios and Gibbs energy with specified units. Medicinal chemistry measures pIC50 conversion, an explicitly labeled IC50-based ligand-efficiency proxy, selectivity ratios, supplied property constraints and evidence limitations. Molecular validation measures parsed SMILES, formula, heavy atoms and hydrogen-bond donors. Synthesis reasoning measures route arithmetic, atom accounting, conversion labels and limiting reagents; it does not validate synthetic routes. Literature reliability uses closed synthetic catalogs and supplied measurement discrepancies. Stress tasks address false premises, invalid valence, salts, concentration units, unassigned stereochemistry and missing reference fixtures.

Spectroscopy, molecular generation, advanced SAR, reaction prediction, retrosynthesis feasibility and expert safety assessment remain unimplemented scientific domains. A full ChemAgent Index must not be inferred from the starter score.

## Data provenance

All released tasks are original synthetic material under CC0-1.0. Code and documentation are MIT licensed. There are no restricted NIST, SWGDRUG, publisher or proprietary datasets. Deliberately invalid reference strings are labeled adversarial fixtures rather than citations. DOI and bibliographic source fields remain null where no real source exists.

Future datasets require a source-specific license audit, a documented curation process, meaningful train/development/test separation and authorizations for any restricted material. A private data store boundary is implemented outside the repository. There are no private items in this release, and no encryption or enterprise access-control claim is made.

## Evaluation methodology

The runner loads validated tasks and constructs public requests containing task identifier, prompt, supplied inputs and output schema. Reference answers and scoring rules are not sent to the provider. The mock provider solves the public inputs through deterministic rules and RDKit, then injects deterministic errors according to model ID, task ID and seed. Local open-model runs use Ollama with the task schema as constrained JSON output. Model digest, runtime version and effective generation settings are retained. The five-task smoke mode produces task evidence without a full-benchmark aggregate or ranking eligibility.

Responses are captured verbatim with a content hash. A strict parser rejects malformed JSON, duplicate keys, nonfinite JSON constants, oversized responses and invalid envelopes. Unknown answer keys cause a format failure; missing answer fields earn no credit. Provider transport failures retain partial run state rather than entering rankings. Successful task checkpoints survive resume. Resume requires matching model/provider identity, benchmark, policy, code, dependencies and execution settings. A PostgreSQL advisory lock or local POSIX lock prevents concurrent writers to a run.

## Automated validation

Typed-field rubrics use exact equality for booleans, strings and lists. Numeric credit is 1 within absolute tolerance. Beyond tolerance, credit decreases linearly to zero over five additional tolerance units. Capability scores are weighted means of field credits multiplied by 100. Each discrepancy records the expected value, observed value, absolute magnitude where applicable, credit and severity.

RDKit computes molecular syntax/sanitization validity, canonical isomeric SMILES, InChI, formula, molecular weight, cLogP, TPSA, QED, donors, acceptors, rotatable bonds, ring counts, Murcko scaffolds and Morgan fingerprint similarity. Salt fragments, charges, isotopes and unspecified stereochemistry are diagnostic flags, not automatic declarations of invalidity. Descriptor computation does not establish synthetic feasibility, activity or safety. Parsing and arithmetic failures are structured results rather than application crashes.

Reference validation in this release is closed-fixture membership and metadata comparison. It does not contact Crossref, PubMed or other live services, and cannot establish global DOI existence, citation entailment or literature completeness.

## Human evaluation

No expert reviewer scores are included. The synthetic tasks are marked pending expert review. Advanced medicinal-chemistry and synthesis tasks should use independent blinded reviewers, preregistered rubrics, calibration examples, adjudication rules and an inter-rater agreement analysis. Inter-rater kappa or alpha is not computed here because no real human-rating observations exist. A schema or future interface cannot substitute for a conducted review.

## Statistical analysis

The starter score is the equally weighted mean of its six category means. Every category must be present; absent categories are not silently renormalized. Category weights and scoring settings are stored in versioned YAML and hashed with the run. Reliability and reproducibility proxies remain separate from the capability composite to avoid double-counting task errors.

Within each category, template clusters are sampled with replacement. All tasks in a sampled cluster are retained, including repeated clusters. For each of 2,000 seeded resamples, category means and the fixed-weight composite are recalculated. Confidence limits are the 2.5th and 97.5th percentiles; bootstrap standard errors are also reported. Task-level sample variances, task counts and cluster counts are exposed. Fewer than two independent clusters yields no interval.

Paired comparison requires identical complete task sets, task grouping and run cohort. Paired task differences are resampled using the same cluster draws. Output includes the weighted mean difference, 95% interval, task win/loss/tie counts, and a standardized paired task effect when its denominator is nonzero. The bootstrap proportion of positive differences is descriptive and is not presented as a calibrated frequentist p-value. A difference interval containing zero is inconclusive. No multiple-testing-adjusted best-system claim is made.

Intervals represent variation over this synthetic collection. They do not capture the full uncertainty from benchmark construction, expert ambiguity, provider nondeterminism, model updates or population validity. Repeated stochastic evaluations require an additional hierarchical level and are future work.

## Reliability measurement

For task i, let each expected field j have correctness credit c_ij and severity s_ij. Let u_i count unsupported citation entries relative to the closed evidence fixture. Define:

E_i = min(1, [Σ_j s_ij(1 − c_ij) + 5u_i] / Σ_j s_ij).

The denominator is fixed by the task rubric, preventing extra citations from diluting errors. Let y_i=1 only when all required fields receive full credit and no citation is unsupported; otherwise y_i=0. Let p_i be reported confidence and B_i=(p_i−y_i)². Invalid responses receive E_i=B_i=1.

CRI = 100 × [1 − 0.8 mean(E_i) − 0.2 mean(B_i)].

This bounded continuous reliability proxy combines severity-weighted discrepancies and confidence calibration. Missing fields count as errors, so blanket abstention does not receive high credit. The weights are normative research choices awaiting independent review. The resulting CRI does not measure all hallucinations, fabricated experimental outcomes or source misrepresentation.

A separate reproducibility checklist awards 40 points for valid structured output, 20 for a nonempty reasoning summary, 20 for explicit uncertainty metadata, and 20 for required unit correctness or nonapplicability. This is metadata completeness, not experimentally demonstrated reproducibility. Run-level provenance is exposed separately.

## Limitations

The benchmark is small, synthetic, public and template-based. Some categories contain few independent clusters. Objective fixtures favor constrained answers and cannot represent expert scientific decision-making. Local open-model evaluations are available; mock behavior remains known by construction and is labeled separately. The implementation uses a local rate limiter and preview submission token, not full authentication or multi-tenant security. Snapshot immutability is enforced by application interfaces, not cryptographic external custody.

Ollama supports digest-pinned local inference. Commercial provider adapters remain explicit extension points. Arena voting, expert review workflows, organization accounts, live evidence verification, billing and enterprise isolation are not operational products in this release.

## Benchmark contamination

All public tasks carry high contamination risk. They are appropriate for software development and reproducibility demonstrations, not as the sole basis of competitive claims. Future hidden sets should document creation dates, source exposure and curation procedures; rotate compromised tasks under new versions; and disclose contamination uncertainty. Private storage alone cannot prove a task was absent from model training.

## Ethics

Do not infer clinical efficacy, safe chemical handling or experimental feasibility from these scores. Do not include actionable hazardous-procedure content merely to expand task coverage. Safety tasks should assess recognition of unsafe, impossible or unsupported premises through suitably bounded prompts. Dataset restrictions and researcher privacy must be respected. Fluency is never a substitute for evidence, and unsupported citations must remain visible failures.

## Governance

Method changes require version control and documented comparability decisions. Maintainer-developed systems use identical rules and explicit conflict disclosures. Sponsors must not influence rankings. Scientific validation requires independent chemistry review beyond code testing. The current release establishes policies and infrastructure; it does not claim an existing independent certification board.

## Future development

Priority work is independently reviewing the starter tasks, extending provider contracts, conducting repeated stochastic evaluations, building live evidence services with failure/uncertainty states, and developing advanced expert-reviewed chemistry benchmarks. Public researcher accounts and review workflows should follow a security design review. Arena preference rankings must remain statistically and visually separate from objective benchmark rankings.

## Implementation references

- RDKit Python documentation: https://www.rdkit.org/docs/GettingStartedInPython.html
- RDKit fingerprint generator API: https://www.rdkit.org/docs/source/rdkit.Chem.rdFingerprintGenerator.html
- Alembic migration tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Next.js application setup: https://nextjs.org/docs/app/getting-started/installation

These sources document implementation tools; they do not validate this benchmark's scientific methodology. No paper DOI or empirical result has been invented.
