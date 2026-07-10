# ADR 0002: Deployment and Execution Strategy

- Status: Accepted
- Date: 2026-07-10

## Context

Molecule Atlas serves several operationally different audiences. An individual researcher should be
able to use it on a laptop or workstation. Most small laboratories and biotechnology teams need a
shared browser application but may have only one Linux server or VM and no Kubernetes operator.
Research IT groups and larger organizations may already have k3s or Kubernetes platforms. Heavy
scientific computation may instead belong on a remote GPU provider or an institutional Slurm
cluster, regardless of where the web application runs.

Treating Kubernetes as the default would impose unnecessary operational work on many primary users.
Treating Docker Compose as the only production topology would make cluster integration, multi-node
scheduling, and institutional policy harder. Coupling scientific execution to either packaging
choice would also leak infrastructure concerns into application and scientific contracts.

## Decision

Molecule Atlas will support three application-deployment profiles:

1. **Personal:** Docker Compose or native development on a laptop or workstation, with useful
   offline and lightweight behavior and no Kubernetes or GPU requirement.
2. **Team Server:** a production-oriented Docker Compose deployment on one Linux server or VM. This
   is the recommended shared deployment for most laboratories and small teams. It includes
   documented HTTPS integration, authentication, durable storage, health checks, restart behavior,
   backup/restore, migrations, and upgrades as their owning milestones arrive.
3. **Cluster:** a Helm deployment for k3s or another conformant Kubernetes platform. This is the
   advanced option for organizations that already need cluster scheduling, policy, reconciliation,
   or multi-node operation; it is not a prerequisite for a shared installation.

Application deployment and scientific execution are orthogonal. The provider-neutral executor
contract selects among fixture/replay, local OCI, Kubernetes Job, remote GPU, and Slurm execution.
Availability depends on explicit operator configuration, credentials, authorization, risk policy,
and budget—not on an assumption derived from Compose or Helm packaging.

Examples of valid topologies include:

```text
Team Server Compose → local OCI executor
Team Server Compose → remote GPU executor
Team Server Compose → institutional Slurm agent
Cluster Helm        → Kubernetes Job executor
Cluster Helm        → remote GPU executor
Cluster Helm        → institutional Slurm agent
```

Not every combination must be enabled or supported at the same milestone. Each executor lands only
when its roadmap milestone owns the implementation and conformance tests.

Official Compose and Helm packaging will reuse the same immutable application images, schema
migrations, health endpoints, application configuration concepts, capability layer, run model,
artifact contracts, and scientific plugin contracts. Ingress, volumes, storage classes, service
accounts, secrets, and provider credentials remain deployment-specific adapters or configuration.

A public demonstration is a configured use of one of these profiles, not a separate application
architecture. Single-node k3s is not described as highly available merely because it uses
Kubernetes; high availability requires redundant control-plane, database, storage, ingress, and
backup design.

## Consequences

Positive consequences:

- most laboratories receive a practical shared deployment without becoming Kubernetes operators;
- institutions can use their existing Kubernetes, remote GPU, or Slurm infrastructure;
- the portable core, application capabilities, plugins, and evidence model remain infrastructure
  independent;
- Compose and Helm installations behave as one product rather than separate implementations;
- scientific execution can evolve without forcing users to move the web control plane.

Costs and constraints:

- production Compose requires maintained backup, restore, upgrade, security, and health-check
  guidance rather than only a development `compose.yaml`;
- Helm packaging and a k3s smoke path add a second supported operational surface;
- release and configuration parity must be tested deliberately;
- executor credentials and policies require clear security boundaries in every topology;
- single-host deployments cannot promise host-level high availability.

## Deferred decisions

This ADR does not select a reverse proxy, identity provider, backup product, PostgreSQL topology,
Kubernetes storage class, observability stack, or remote execution provider. It does not require
deployment manifests before their roadmap milestones. Those choices should be made from concrete
operator needs while preserving this separation between application deployment and scientific
execution.
