# AI-First Readiness

## Status and objective

Molecule Atlas is a reliable scientific application first. It should also expose its important
operations through boundaries that a future AI agent can invoke safely, with the same validation,
authorization, execution, provenance, and audit behavior as the React UI.

The governing design rule is:

> Can this operation be represented as a typed, authorized, observable, reproducible application
> capability that both a human UI and a future AI agent can invoke?

AI-first readiness does not mean implementing an LLM now. It means avoiding hidden UI state, direct
database access, implicit side effects, unstructured plugin results, and execution paths available
only to an agent.

## Shared capability boundary

The React UI and a future AI agent are clients of the same application capabilities.

```text
React UI ──HTTP/OpenAPI──┐
                         │
CLI / workers ───────────┼──> Application capabilities
                         │      ├── typed validation
Future AI module ────────┘      ├── authorization and policy
                                ├── plans, runs, and provenance
                                └── domain operations
                                           │
                                           ▼
                              repositories / executors / plugins
```

The transport may differ. The UI usually calls through FastAPI; an in-process AI module or worker
may call the capability layer directly. The validation, policy, and side-effect boundary must not
differ.

The future AI layer may propose, plan, choose among allowed capabilities, and explain evidence. The
backend validates, authorizes, persists, executes, limits, and audits. An agent must never:

- query PostgreSQL or object storage directly;
- invoke scientific containers or provider APIs directly;
- bypass capability-level permissions or approval policy;
- create a separate run or workflow model;
- encode important scientific conclusions only in chat history;
- be recorded as if it were the delegating human.

Scientific plugins remain independently versioned tools. AI logic does not belong inside RDKit,
Meeko, Vina, PoseBusters, ProLIF, Boltz, DiffDock, or their plugin adapters.

## Application capability contract

A capability is a meaningful application operation, not an HTTP route and not an arbitrary CRUD
method. Examples include:

```text
import_compound_library
standardize_compound_set
run_similarity_search
import_evidence_run
validate_pose_set
compare_candidates
create_candidate_shortlist
generate_campaign_report
record_scientific_decision
```

Each capability definition should expose stable, machine-readable metadata:

```text
capability_id
capability_version
kind
title
description
input_schema
output_schema
required_permissions
risk_level
side_effects
estimated_cost_class
estimated_runtime_class
supports_idempotency
supports_cancellation
supports_dry_run
```

Capability identifiers use stable `snake_case` names and must not change merely because a URL,
module, or implementation changes. FastAPI endpoints that expose a capability set an explicit
`operation_id` equal to the capability ID, or to a stable transport-specific derivative when more
than one endpoint exposes the same capability.

Capability input and output models are explicit, versioned Pydantic contracts. Avoid generic
`options`, `files`, or arbitrary dictionaries where the domain can be described directly. Input
contracts identify stored entities or artifacts and make parameters, random seeds, and limits
explicit. Output contracts return stable IDs, counts, warnings, and semantic artifacts rather than
filenames alone.

CRUD operations can remain internal implementation details. They are not automatically registered
as capabilities and must not automatically become agent tools.

## Invocation semantics

Every exposed operation has one clear semantic kind:

| Kind | Meaning | Example |
| --- | --- | --- |
| Query | Bounded read with no state change | `get_run_summary` |
| Command | Explicit synchronous state change | `create_candidate_shortlist` |
| Job | Asynchronous command represented by a run | `start_docking_campaign` |
| Proposal | Suggested state change requiring validation or approval | `propose_candidate_shortlist` |

Avoid generic endpoints such as `/execute`, `/run`, and `/update`. Use domain-specific operations.
Agent-facing operations should be task-oriented and coarse enough that the caller does not need to
coordinate fragile sequences of low-level CRUD calls.

High-value bounded queries should include project snapshots, run summaries, artifact listings,
candidate evidence, unresolved validation issues, recent decisions, campaign status, and selected
candidate comparisons. They should aggregate and paginate instead of exposing entire database tables
or thousands of raw records by default.

## Semantic artifacts and provenance

Agents, users, and workflows discover artifacts by type and metadata, never by guessing filenames.
The current portable artifact contract is the starting point. Before persistent storage or managed
execution, evolve it through an explicit schema version to include:

```text
artifact_id
artifact_type
schema_version
media_type
semantic_role
storage_uri
content_digest
size_bytes
project_id
producing_run_id
derived_from_artifact_ids
created_at
domain_metadata
preview_metadata
```

Useful semantic artifact types include:

```text
compound-set
standardized-compound-set
descriptor-table
similarity-matrix
cluster-assignment
protein-structure
prepared-pocket
docking-pose-set
docking-score-table
interaction-fingerprint
validation-report
candidate-ranking
candidate-shortlist
campaign-report
execution-notebook
```

Plugin results declare a result type and semantic artifact inventory. Raw upstream outputs remain
artifacts and normalization records retain their source artifact, field, adapter, and schema version.

Provenance is represented by relationships, not only logs:

```text
Run used Artifact A
RunAttempt used Plugin P version V and image digest D
RunAttempt generated Artifact B
Artifact B was derived from Artifact A
ValidationResult evaluated Artifact B
Decision X was informed by Evidence E
Claim C was supported or contradicted by Evidence E
```

## Plans, runs, attempts, and provider jobs

Molecule Atlas uses one generic hierarchy for imported evidence, capabilities, reports, scientific
plugins, model inference, generated-code execution if ever added, and future agent actions:

```text
Capability
    → PlanStep
    → Run
    → RunAttempt
    → Artifact
    → ValidationResult
    → Evidence
    → ScientificClaim
    → ScientificDecision
```

Definitions:

- `Capability`: a meaningful application operation.
- `PlanStep`: a versioned, configured invocation of a capability.
- `Run`: the logical record of one capability invocation, possibly with multiple attempts.
- `RunAttempt`: one concrete import or execution attempt, including retries and provider details.
- `Artifact`: a typed, content-addressed input or output.
- `ValidationResult`: structured quality or correctness evidence.
- `Evidence`: information supporting or contradicting an interpretation.
- `ScientificClaim`: a reviewable scientific interpretation.
- `ScientificDecision`: a human-owned project decision with rationale and supporting evidence.

A provider job is operational data attached to a run attempt. It is not a second scientific result
model. An imported result also creates a run and an import attempt; it does not require a managed
provider job.

The target `Run` relationship fields include:

```text
run_id
project_id
run_type
capability_id
capability_version
status
actor
parent_run_id
root_run_id
plan_id
plan_step_id
input_manifest_id
output_manifest_id
idempotency_key
correlation_id
causation_id
created_at
started_at
completed_at
error_code
error_details
```

`RunAttempt` adds attempt number, executor/provider identity, provider job ID, retry relationship,
runtime, exact plugin/container identity, logs, failure details, and attempt-specific artifacts.

The implemented run-manifest schema `0.1.0` remains the portable evidence snapshot for Milestone 1.
Do not silently add required hierarchy or persistence fields to it. Introduce a documented schema
version and migration strategy when later milestones require the shared run/attempt model.

## Plans and approvals

Plans are introduced before an LLM. Initially they may be created by predefined workflows or the UI.
A future agent proposes the same structure.

```text
Plan
- id, project_id, objective, status, version
- created_by, constraints, budget, created_at

PlanStep
- id, plan_id, capability_id, capability_version
- input_bindings, dependencies, status, approval_policy
```

Execution always follows:

```text
Predefined workflow or future AI proposal
    → typed Plan
    → schema and dependency validation
    → permission, risk, and budget evaluation
    → required human approval
    → normal backend execution
```

Plans must support waiting for approval and resuming later. Chat content may explain a plan but is not
the plan's source of truth.

## Actors, authorization, risk, and limits

Audit records distinguish `human`, `service`, `plugin`, and `agent` actors. An agent action records
the agent/version, model provider and identifier, delegating user, granted permission scope, agent
run, tool calls, and approval records where applicable.

Authorization is enforced inside the capability boundary. UI visibility is not authorization. An AI
module receives narrowly scoped capability access, never database, object-storage, cluster, or cloud
provider credentials.

Every side-effecting capability declares risk and approval metadata. Suggested policies include:

| Operation | Default policy |
| --- | --- |
| Read bounded project metadata | Automatic when authorized |
| Calculate local descriptors | Automatic within configured limits |
| Run a small CPU analysis | Automatic within budget |
| Start a large GPU job | Approval above policy threshold |
| Call a paid external API | Explicit approval |
| Modify an accepted shortlist | Human approval |
| Delete project data | Never automatically authorized |
| Submit an experiment | Mandatory human approval |

Commands that create runs, jobs, artifacts, imports, reports, shortlists, or external calls accept an
idempotency key. Retrying the same authorized command with the same key must not duplicate work.

Plans and runs can carry maximum steps, retries, runtime, CPU/GPU usage, external cost, artifact size,
parallelism, and generated-code limits. The backend rejects or pauses work that exceeds policy.

## Typed events and observability

Domain events are typed, versioned facts. Example event types include:

```text
run.created.v1
run.started.v1
run.progressed.v1
run.failed.v1
run.completed.v1
artifact.created.v1
validation.issue_detected.v1
plan.proposed.v1
plan.approval_required.v1
plan.approved.v1
decision.recorded.v1
```

The event envelope carries `event_id`, `event_type`, `occurred_at`, `project_id`, `correlation_id`,
`causation_id`, actor, and a typed payload. Persisted state remains the source of truth. SSE publishes
events for browser updates but is never the durable workflow state.

Correlation and lineage identifiers trace:

```text
HTTP request or agent invocation
→ capability
→ plan and plan step
→ run and attempt
→ dispatcher and executor
→ plugin
→ artifact upload
→ validation and decision
```

Sensitive scientific inputs should not be copied into logs merely for observability.

## Scientific memory and UI parity

Scientific conclusions are explicit project records, not chat memory. A `ScientificClaim` records its
statement, type, status, confidence semantics, supporting and contradicting evidence, proposer,
reviewer, and supersession relationship. Claim statuses include `proposed`, `accepted`, `rejected`,
`uncertain`, and `superseded`.

A `ScientificDecision` records selected candidates or actions, rationale, rejected alternatives,
owner, evidence, AI contribution, human approval, and timestamp. A model prediction alone cannot
create an accepted scientific claim or human-owned decision.

Every agent-invocable operation and its result must remain inspectable in the normal UI. Users should
be able to see the objective, plan, capabilities, inputs, parameters, plugin/model identity,
artifacts, failures, validation issues, evidence, AI proposals, approvals, and reproduction details
without consulting chat history.

## AI module placement

Keep the modular monolith. A future AI module may initially live in the FastAPI application and call
the application capability layer in process. Extract it only for demonstrated needs such as security
isolation, independent scaling, multiple agent workers, or provider-specific runtimes.

Do not introduce a vector database, graph database, MCP server, multi-agent system, autonomous web
research, prompt-management platform, long-term chat memory, provider-specific agent framework, or
generated-code execution before a concrete accepted milestone requires it.

## Staged delivery

| Roadmap stage | AI-readiness obligation |
| --- | --- |
| Milestone 1 | Typed evidence, hashes, provenance, partial/failed states, validation, human-readable inspection. Implemented. |
| Milestone 2 | Typed adapter contracts, semantic artifact types, explicit lineage, real-output replay fixtures. |
| Milestone 3 | Shared application capability layer, thin HTTP handlers, stable IDs and `operation_id` values, typed inputs/outputs, bounded queries, correlation IDs. |
| Milestone 4 | Protein/pocket/pose actions use capabilities and typed artifacts; no viewer-only scientific state. |
| Milestone 5 | PostgreSQL-backed actors, authorization, hierarchical runs/attempts, plans/steps, idempotency, typed events, artifact relationships, claims, and decisions. |
| Milestone 6 | Durable workflow progression, retries, cancellation, resume, approvals, risk policies, budgets, workflow templates, and end-to-end tracing. |
| Milestones 7–9 | The same capabilities and run model across Kubernetes, remote GPU, and institutional executors; provider credentials remain infrastructure-only. |
| Milestone 10 | Governed AI planning and explanation over existing capabilities, plans, policies, and bounded context queries. |
| Milestone 11 | Generative or advanced scientific workflows only after screening, review, and governed orchestration are trusted. |

## Feature readiness review

Before implementing an important feature, answer:

1. What is the capability ID, version, and semantic kind?
2. Are input and output contracts explicit and versioned?
3. Can the React UI and a future authorized agent use the same capability?
4. Are side effects, idempotency, cancellation, risk, approval, cost, and runtime declared?
5. Does authorization run inside the capability boundary?
6. Is the operation represented by the shared plan/run/attempt model when applicable?
7. Are artifacts typed, content-addressed, and connected by explicit lineage?
8. Are validation failures and missing provenance retained?
9. Are actor, correlation, causation, and parent/root relationships observable?
10. Can the normal UI inspect and reproduce the outcome without chat history?

If the milestone does not yet contain the required persistence or execution substrate, document the
future contract and implement only the smallest boundary required by the current acceptance criteria.
