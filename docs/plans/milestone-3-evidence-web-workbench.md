# Milestone 3 Implementation Plan: Evidence Web Workbench

- Status: In progress
- Current slice: Slice 1 implemented; Slice 2 — safe local import — is next
- Roadmap milestone: 3 — Evidence import in the web workbench
- Planning date: 2026-07-11

## Outcome

Molecule Atlas will accept a portable evidence bundle, validate and retain its manifest and
referenced artifacts in bounded local storage, and let a researcher review the run, provenance,
typed predictions, validation evidence, and candidate relationships in the browser. The React UI,
FastAPI transport, tests, and a future authorized AI client will all use the same typed application
capabilities.

This milestone remains local and offline. It does not add PostgreSQL, authentication, durable jobs,
Kubernetes, GPU execution, external model inference, plugin execution in FastAPI, or AI/agent code.
Local imports are explicitly temporary and are not presented as durable project history.

## Design pass

The existing ligand workbench remains the default **Candidates** workspace. A top-level workspace
switch adds **Evidence runs** without moving or replacing the current table, chemical-space plot,
candidate details, or 3D conformer viewer.

The evidence workspace uses a review-oriented master/detail layout:

- an import action and compact run list on the left;
- a run header with succeeded, partial, failed, cancelled, or unknown state;
- summary, provenance, predictions, validation, and artifacts sections in the main pane;
- a candidate-evidence section that links manifest scope identifiers to candidates when a binding
  can be established explicitly;
- a comparison tray for two or more compatible candidates, poses, or methods;
- prominent failed/error validation rows that remain inspectable alongside their raw sources;
- visible empty, importing, invalid-bundle, partial-run, failed-run, and unavailable-artifact states.

Normalized scientific values are never displayed as an unqualified score. Each prediction card
shows its typed label, value and unit, optimization direction, scope, method reference, raw artifact
and field, interpretation, uncertainty, and caveats. Comparison groups like prediction types only;
it does not synthesize a universal rank.

ZIP is a transport envelope for browser upload, not a new scientific contract. Its root contains
`molecule-atlas-run.json`, optional `molecule-atlas-artifacts.json`, and the referenced relative
artifact paths. Import rejects traversal, links, duplicate members, encrypted members, excessive
member counts, and configured compressed/uncompressed size limits before extraction. Extracted
bytes are audited through the existing portable core and are never executed.

## Capability catalog

All definitions use stable snake-case IDs, semantic versions, strict versioned Pydantic inputs and
outputs, and explicit metadata. Only these task-oriented operations become capabilities; local
repository CRUD and ZIP extraction helpers remain internal.

| Capability | Kind | Initial policy | Typed result |
| --- | --- | --- | --- |
| `import_evidence_bundle` `0.1.0` | command | local write, medium risk, idempotency supported | imported run reference plus audit/import warnings |
| `get_run_summary` `0.1.0` | query | read-only, low risk | bounded run/method/count/failure summary |
| `list_available_artifacts` `0.1.0` | query | read-only, low risk | bounded semantic and portable artifact records |
| `get_candidate_evidence` `0.1.0` | query | read-only, low risk | typed predictions and validation linked by explicit scope IDs |
| `compare_candidates` `0.1.0` | query | read-only, low risk | grouped like-for-like evidence for 2–10 subjects |
| `validate_evidence_artifacts` `0.1.0` | query | bounded CPU read, low risk | digest/provenance audit results without plugin execution |
| `generate_evidence_report` `0.1.0` | query | bounded CPU read, low risk | deterministic Markdown or HTML derived from the imported record |

Every definition records title, description, input/output schema identifiers, required permissions,
side effects, risk, cost and runtime classes, idempotency, cancellation, and dry-run support. Initial
local HTTP actor context is explicit and capability authorization checks declared permissions, but
Milestone 5 owns authenticated human actors, persistent grants, durable idempotency records, and
approval policy.

## Acceptance-criterion map

| Milestone 3 criterion | Packages and models | API/CLI/UI | Fixtures and focused tests | Documentation |
| --- | --- | --- | --- | --- |
| Explicit application capability layer | `app/application/capabilities`; `CapabilityDefinition`, `CapabilityContext`, permission policy and catalog | HTTP depends on capability objects; no route-local workflow | catalog uniqueness, authorization, architecture import tests | architecture and this plan |
| Stable IDs, versions, metadata, and semantic kinds | strict enums and definition records in the capability catalog | explicit OpenAPI `operation_id` equal to capability ID | exact metadata golden assertions and OpenAPI checks | capability table above and scientific contracts |
| Typed versioned inputs/outputs | `app/application/evidence/contracts.py`; no loose `options` dictionaries | generated OpenAPI TypeScript types consumed by React | strict-model rejection and JSON round trips | scientific contracts examples |
| Thin FastAPI handlers | `app/api/evidence.py`; application errors mapped to documented HTTP responses | multipart parsing/correlation headers only in routes | dependency-injected endpoint tests plus architecture ownership rules | architecture current-state update |
| Query/command/job/proposal semantics | `CapabilityKind`; catalog contains commands and queries only in this milestone | no ambiguous `/run` or `/execute` route; no jobs/proposals claimed | catalog semantics tests | AI-first readiness cross-reference |
| Upload manifest and referenced artifacts | local ZIP ingress adapter and bounded local evidence repository; `ImportEvidenceBundleInput/Output` | `POST /api/evidence/imports`, `operation_id=import_evidence_bundle` | tiny valid, traversal, oversized, duplicate, invalid-manifest, missing/mismatch fixtures | README upload format and temporary-storage warning |
| Run summary and provenance | `RunSummary`, `MethodSummary`, warning/failure summaries | `GET /api/evidence/runs/{run_id}`, `operation_id=get_run_summary`; summary/provenance sections | succeeded, partial, failed, missing provenance | README and UI copy |
| Typed prediction panel | `PredictionEvidence` preserves the core discriminated union | prediction cards with source/method links | every prediction type, units, caveats, no generic score | scientific contracts UI projection |
| Validation evidence panel | `ValidationEvidenceSummary`; core `ValidationResult` unchanged | status-filterable table; fail/error visually prominent | pass/fail/warning/unavailable/error states and raw source preservation | README caveats |
| Candidate/run relationship | explicit local `CandidateEvidenceBinding` derived only from recorded scope/upstream IDs | linked candidate evidence section; unbound state remains visible | bound and intentionally unbound scope fixtures | domain model relationship note |
| Compare at least two poses/methods | `CompareCandidatesInput/Output`, typed comparison groups | selection tray and comparison view | 2 minimum, 10 maximum, incompatible types remain separate | UI behavior and scientific caveat |
| Bounded context queries | four named query handlers and explicit result/page limits | stable routes for summary, artifacts, candidate evidence, comparison | limit enforcement, not-found, no raw database/filesystem enumeration | AI-readiness bounded-query section |
| Correlation identifiers | ephemeral `CapabilityContext` and response metadata; no persistent run fields invented | accept/validate `X-Correlation-ID`, return it in body/header | supplied/generated/invalid identifiers | architecture notes temporary semantics |
| Partial and failed states | existing `RunMetadata`/`RunFailure` projected without rewriting | state banners, missing outputs, failure detail | succeeded/partial/failed fixture UI and API tests | README caveats |
| UI uses shared contracts | generated `openapi.d.ts`; evidence feature API/client/components | Candidates and Evidence runs workspaces | Vitest loading/empty/error/partial/failed tests and Playwright import/review/compare flow | README screenshots deferred; usage documented |
| Preserve current behavior and CI gates | existing packages stay in place; new imports follow enforced directions | current candidate endpoints and workbench remain unchanged | full pytest, Ruff, format, strict Pyright, frontend lint/test/build, OpenAPI check, Playwright | update commands only if they truly change |

The portable CLI keeps its existing `adapters`, `audit`, `inspect`, `schema`, and `report` behavior.
ZIP is HTTP ingress rather than a second evidence schema, so no new core CLI command is required for
Milestone 3. Replay continues through the existing manifest adapter and tiny checked-in fixtures.

## Incremental slices

1. **Capability foundation and run summary** — definition/catalog contracts, context and permission
   check, local read port/adapter, `get_run_summary`, thin endpoint, correlation ID, OpenAPI contract.
2. **Safe local import** — bounded ZIP parsing, temporary repository, audit, idempotency within the
   process lifetime, import endpoint, invalid-bundle fixtures and tests.
3. **Artifact and validation inspection** — `list_available_artifacts` and
   `validate_evidence_artifacts`, digest status, semantic artifact binding, raw-source links.
4. **Candidate evidence query** — explicit candidate/run bindings and typed prediction/validation
   projections with strict bounds.
5. **Scientific comparison and reports** — like-for-like `compare_candidates` plus deterministic
   report capability; no combined score or implicit ranking.
6. **Evidence runs UI** — design-system additions, run list/detail, provenance, typed predictions,
   validation and artifact states while preserving the Candidates workspace.
7. **Import and comparison UI** — upload progress/errors, candidate/run links, comparison tray,
   responsive and accessible states.
8. **Conformance and documentation** — Playwright evidence workflow, generated contracts, all CI
   gates, README/architecture/domain/scientific-contract updates, roadmap completion review.

Each slice begins with a focused failing test, implements the smallest coherent behavior, updates
contracts/documentation in the same change, and leaves the worktree uncommitted unless the user asks
for a commit.
