# Molecule Atlas MVP Frontend Design

## Design Goal

Build a quiet, information-dense scientific workbench for reviewing a small-molecule candidate set. The first screen is the product experience, not a landing page.

## Primary Layout

- Header bar: app name, candidate-set name, valid/invalid counts.
- Main split:
  - Left: candidate table with sort and filter controls.
  - Right: selected candidate detail panel.
- Lower or secondary view: chemical-space projection after the core table/detail loop works.

## Candidate Table

Columns:

- status;
- name;
- score;
- molecular weight;
- LogP;
- TPSA;
- HBD;
- HBA;
- rotatable bonds;
- Lipinski violations;
- scaffold.

Interactions:

- click row to select;
- sort numeric columns;
- filter valid molecules only;
- text search by name or SMILES.

## Detail Panel

Sections:

- 2D structure;
- 3D conformer tab;
- canonical SMILES;
- descriptor grid;
- triage flags;
- nearest neighbors;
- validation notes.

## Visual Style

- restrained scientific UI;
- no marketing hero;
- no decorative gradient blobs;
- stable split-panel dimensions;
- dense enough for scanning but not cramped;
- color used for state and flags, not decoration.

## MVP Acceptance Criteria

- A user can load the demo candidate set and immediately understand the selected molecule.
- Invalid SMILES are visible and non-fatal.
- Similarity neighbors are visible for valid candidates.
- 2D and 3D molecule views are clearly distinguished.
- The UI does not imply that conformers are binding poses.

## Browser Verification

Use Playwright e2e tests for browser-level verification. The minimum e2e suite starts the frontend against the local backend and verifies:

- the workbench loads the demo candidate set;
- selecting a row updates the detail panel;
- invalid SMILES rows are visible without crashing the app;
- the 3D conformer tab opens for valid molecules;
- the chemical-space section renders;
- the 2D/3D labels make clear that generated conformers are not binding poses.
