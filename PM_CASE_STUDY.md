# GaiaDNA: From an AI discovery concept to a biodiversity review tool

**Context:** Hackathon project, adapted into a recruiter-facing portfolio demo.

**Stage:** Colab prototype → deployable MVP. Public launch and user validation are pending.

## Product opportunity
Biodiversity occurrence datasets contain records with incomplete taxonomic identification. GaiaDNA explores a focused question: can a lightweight interface help a researcher find, inspect and export those records for expert review?

The original vision combined “ghost species” detection, discovery prediction and conservation maps. Inspection of the prototype surfaced a product risk: a missing species label was being presented as evidence of an undiscovered species. The revised MVP makes the evidence visible and narrows its promise to record triage.

## Intended users and job to be done
**Primary user hypothesis:** biodiversity researchers or collection data curators reviewing occurrence datasets. **Secondary hypothesis:** students exploring taxonomic data quality. These personas have not yet been validated through interviews.

“When I receive an occurrence dataset, help me isolate records with incomplete identification, understand where they were recorded, and export a review queue so I can decide what needs expert attention.”

The proposed benefit is less manual filtering and a clearer handoff to experts. No time savings have yet been measured.

## Evidence from the supplied project
The source materials include a Colab notebook, two data files and a description of a Streamlit dashboard. A direct audit of the supplied fungi file found:

| Observed measure | Records |
| --- | ---: |
| Total occurrence records | 30,091 |
| Genus present, species blank | 8,190 |
| Species field populated | 6,908 |
| Both genus and species blank | 14,993 |

These categories describe metadata completeness, not unique species, verified discoveries or ecological importance. The insects example contains 500 records, of which 138 have genus present and species blank; its provenance is unverified.

The notebook generates environmental variables and explores classification models. It does not establish real-world discovery accuracy. No user interviews, adoption metrics, field validation or conservation outcomes were available in the supplied evidence.

## Product decision: earn trust before adding prediction
The MVP prioritizes an observable task: review incomplete records. This trades a more ambitious AI story for an interpretable workflow that can be tested with users.

| Decision | Reason | Tradeoff |
| --- | --- | --- |
| Keep rules visible | Users can understand why a record was flagged | No prediction of novel species |
| Separate missing genus from missing species | Different gaps require different review actions | Adds a third status to explain |
| Include bundled datasets | First-time visitors can try the workflow immediately | Sample provenance needs explicit context |
| Filter, map and export | Supports a complete review handoff | Does not resolve identification itself |
| Label AI as an identification-gap experiment | Separates measured classification scores from unvalidated discovery claims | Scientific discovery remains a research direction |

## MVP experience
1. Open a sample dataset or upload a CSV/TSV.
2. Review counts for three identification statuses.
3. Filter records by status and genus.
4. Inspect valid locations and genus counts.
5. Export a review queue with original source and attribution fields.

Input validation handles missing columns, empty files and invalid coordinates. Maps and tables have display limits while exports retain the full filtered selection. The app does not require a running Colab session.

## Validation plan
Recruit five intended users for an initial formative usability study; recruitment is proposed, not completed. Ask each participant to identify incomplete records in a provided dataset and prepare a review queue, first using their usual workflow and then GaiaDNA. Counterbalance task order and use comparable datasets to reduce learning effects.

Measure task completion, elapsed time, filtering errors and whether participants understand that flagged records are not confirmed new species. Ask where an export would fit in their existing research process.

**Proposed success criteria, not achieved results:** at least four of five participants complete the core task without help; median completion time improves by 30% relative to their baseline; all participants correctly explain the meaning of a flagged record. This small study can identify usability issues, not establish population-level impact.

## Metrics and guardrails
- **Primary proposed metric:** successfully prepared review queues per active researcher, paired with researcher confirmation that the queue is useful.
- **Activation:** percentage of visits completing dataset load → filter → export.
- **Efficiency:** median time to a correct review queue compared with the baseline workflow.
- **Trust:** percentage correctly distinguishing incomplete identification from discovery evidence.
- **Guardrails:** parsing failures, mislabeled review statuses, lost attribution and accidental sharing of sensitive coordinates.

Analytics and user feedback collection have not yet been implemented. Export events alone would not establish scientific value.

## Roadmap and release gates
**First release:** validate the review workflow, confirm source attribution, test public deployment and complete five usability sessions.

**Next:** add configurable field mapping and expert annotations if user testing confirms those needs. Prioritize by observed task failure and frequency, rather than assumed demand.

**Later AI experiment:** acquire documented environmental observations and expert-reviewed labels; establish a simple baseline; evaluate precision, recall and calibration with geographic holdouts; assess sampling bias. Predicting missing labels would still be a different task from predicting novel species. Do not present a discovery probability without a defensible target and field validation.

## Outcome and reflection
The tangible outcome at this stage is a deployment-ready review MVP and a clearer product hypothesis. Public availability, adoption and scientific impact remain unverified.

The central learning is that product value depends on matching the claim to the evidence. For GaiaDNA, a transparent review queue is a testable first step toward the broader biodiversity discovery vision.

## Authorship details to finalize before portfolio publication
The author confirmed this was a hackathon project intended for a recruiter-facing demo. Exact responsibilities, team size, project dates and interview history still need confirmation. Add verified details for those items before presenting this as a personal PM case study. Attribute this deployment adaptation and case-study preparation appropriately; do not imply the revised decisions were part of the original project history if they were made later.
