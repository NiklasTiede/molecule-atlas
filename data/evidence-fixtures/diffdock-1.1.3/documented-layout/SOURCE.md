# DiffDock 1.1.3 documented-layout fixture

This is a parser-development fixture, not generated scientific output.

- Upstream repository: <https://github.com/gcorso/DiffDock>
- Upstream release: `v1.1.3`
- Upstream release commit: `9a22cbcbc7612c7565c80e8399d9be298971f156`
- Layout source: `inference.py` at tag `v1.1.3`
- Interpretation source: the `README.md` FAQ at tag `v1.1.3`
- Capture date: 2026-07-11

The SDF files are tiny Molecule Atlas-authored placeholders. Their filenames follow the upstream
writer contract, but their coordinates and confidence values are synthetic and make no claim about
a real protein, ligand, pose, affinity, or biological activity. `rank1.sdf` represents the
unqualified top-pose alias written alongside the confidence-qualified ranked files.

The upstream code and model weights are MIT-licensed. The Molecule Atlas-authored placeholders and
fixture arrangement are provided under CC0-1.0. This fixture verifies documented layout, ranking,
and pose-confidence normalization only. It is not a genuine DiffDock run and does not satisfy
Milestone 2's real-output-fixture criterion.
