# Molecule Atlas Product Vision

## Purpose

Molecule Atlas is an open-source, browser-based workbench for reviewing small-molecule candidate sets.

The project focuses on a practical gap in molecular design workflows: computational systems can generate, dock, score, or prioritize many candidate molecules, but scientists still need a clear interface to inspect structures, compare properties, understand similarity relationships, and review model outputs with appropriate caveats.

Molecule Atlas is not a drug-discovery decision engine. It is a review and triage layer for chemical data.

## Long-Term Vision

In a future molecular design workflow, upstream systems may generate, dock, co-fold, rank, or otherwise prioritize candidate small molecules for a target protein pocket. Those systems might include docking pipelines, foundation-model workflows, GPU-cluster jobs, or AI-assisted molecule generation.

Their output is often a candidate set:

- molecular structures;
- descriptors and fingerprints;
- scores and confidence values;
- provenance and model metadata;
- optional target and protein-pocket context;
- eventually ligand poses and interaction fingerprints.

Molecule Atlas should make those outputs inspectable, comparable, and scientifically interpretable.

Long-term capabilities could include:

- importing candidate sets from external model, docking, or screening jobs;
- validating structures and preserving provenance;
- computing and displaying molecular descriptors, fingerprints, scaffolds, and similarity relationships;
- showing 2D and 3D molecule representations in the browser;
- comparing generated candidates against known ligands or reference molecules;
- visualizing protein-ligand binding poses inside a target pocket;
- surfacing protein-ligand interactions and interaction fingerprints;
- showing predicted affinity, uncertainty, and model confidence without overstating reliability;
- flagging ADME-like, toxicity-like, and synthetic-accessibility concerns as triage signals;
- supporting review workflows where users can filter, annotate, rank, and export candidate molecules.

## Current MVP

The current MVP is deliberately ligand-centric. It proves the core workflow before adding protein structures, docking, model inference, or GPU-backed jobs.

The MVP supports:

- loading a bundled demo candidate set;
- validating and canonicalizing SMILES with RDKit;
- computing common descriptors;
- computing Morgan fingerprints;
- searching by Tanimoto similarity;
- grouping by Murcko scaffold;
- displaying Lipinski and Veber-style triage flags;
- rendering backend-generated 2D molecule depictions;
- generating simple 3D conformers for browser inspection;
- projecting chemical space with PCA;
- keeping invalid SMILES visible and non-fatal.

## Boundaries

The MVP does not:

- run docking;
- run molecular generation models;
- run protein-ligand co-folding;
- orchestrate GPU jobs;
- predict clinical success;
- make medicinal chemistry recommendations;
- claim that candidates are safe, active, synthesizable, or drug-like.

Rule-based filters and demo scores are triage signals only.

## Future Architecture Direction

The data model should continue to center on candidate sets rather than generic molecule tables.

A future candidate record may include:

- `id`;
- `name`;
- `smiles`;
- `canonical_smiles`;
- `source`;
- `target_id`;
- `job_id`;
- `model_name`;
- `model_version`;
- `predicted_affinity`;
- `model_confidence`;
- `pose_file`;
- `protein_structure_id`;
- `provenance`;
- `review_status`;
- `scientist_notes`.

The current app only needs a subset of this, but names and API boundaries should leave room for imported model or docking outputs.

## Open-Source Positioning

Commercial molecular modeling and drug-design platforms are powerful and established. Molecule Atlas should not try to clone them.

The opportunity for Molecule Atlas is different:

- transparent data handling;
- reproducible local workflows;
- browser-native interaction;
- clear scientific caveats;
- understandable architecture;
- easy extension by scientists and software engineers.

The project should stay honest about what is implemented and careful about what is inferred.
