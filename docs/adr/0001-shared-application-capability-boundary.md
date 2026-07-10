# ADR 0001: Shared Application Capability Boundary

- Status: Accepted
- Date: 2026-07-10

## Context

Molecule Atlas is expected to gain optional AI-assisted planning and explanation after its scientific
imports, review workflows, persistence, and execution controls are trustworthy. If UI handlers,
workers, plugins, and a future agent each coordinate domain work differently, the agent would require
privileged access, duplicate business logic, or an incompatible execution model.

The project also needs to avoid prematurely adding an LLM, agent framework, MCP server, vector store,
or autonomous execution before user workflows establish a need.

## Decision

Molecule Atlas will introduce a typed application capability layer between transports and domain or
infrastructure code.

- The React UI and a future AI module are clients of the same capabilities.
- FastAPI handlers remain transport adapters and do not own business workflows.
- Capability definitions have stable identifiers, versions, typed inputs/outputs, permission
  requirements, side-effect semantics, risk metadata, and execution characteristics.
- Authorization, idempotency, approval, budget, and audit policy are enforced at the capability
  boundary as their owning milestones introduce them.
- CRUD methods remain internal and are not automatically exposed as agent tools.
- Scientific plugins remain independently versioned computational tools below the capability and
  run/workflow layers. AI logic does not run inside plugins.
- Imported results, capabilities, plugins, reports, future AI actions, and retries use one conceptual
  `Plan → PlanStep → Run → RunAttempt → Artifact` execution and provenance model.
- Scientific claims and decisions are structured project records. Chat is never their only source of
  truth.
- An AI actor is distinguishable from its delegating human and never receives direct database,
  object-store, executor, cluster, or provider credentials.
- The application remains a modular monolith until a demonstrated scaling or isolation requirement
  justifies extracting an AI service.

The completed portable evidence core remains valid. Its `0.1.0` manifest is an offline evidence
snapshot, not a persisted workflow aggregate. Later hierarchy and semantic-artifact additions require
an explicit version and migration strategy.

## Consequences

Positive consequences:

- UI, workers, automation, and future AI reuse validation and business rules.
- OpenAPI operations can become safe agent tools selectively rather than exposing all CRUD.
- Plans, runs, artifacts, validation, claims, and decisions remain inspectable and reproducible.
- Permissions, approvals, cost limits, and idempotency are backend guarantees rather than prompt
  conventions.
- Scientific plugins stay deterministic and replaceable.

Costs and constraints:

- Capability IDs and contracts become compatibility commitments.
- HTTP handlers may require an additional application-layer abstraction.
- Run/attempt, event, plan, and artifact lineage models require careful migrations when persistence
  begins.
- Not every internal operation should be exposed, so capability registration requires deliberate
  product and security review.

## Deferred decisions

This ADR does not select an LLM provider, agent framework, tool protocol, vector store, workflow
engine, event broker, or AI deployment topology. Those choices require later milestone evidence.
