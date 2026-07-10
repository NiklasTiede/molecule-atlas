# Boltz 2.2.1 documented-layout fixture

This is a parser-development fixture, not generated scientific output.

- Upstream repository: <https://github.com/jwohlwend/boltz>
- Upstream release: `2.2.1`
- Upstream release commit: `cb04aec`
- Layout source: `src/boltz/data/write/writer.py` at tag `v2.2.1`
- Field and interpretation source: `docs/prediction.md` at tag `v2.2.1`
- Capture date: 2026-07-10

The confidence and affinity JSON objects reproduce the illustrative values published in the
upstream prediction documentation. The mmCIF file is a tiny Molecule Atlas-authored placeholder
whose filename follows the upstream writer contract. It is not a Boltz prediction and contains no
claim about a real protein, ligand, pose, affinity, or biological activity.

The upstream repository and documentation are MIT-licensed. The Molecule Atlas-authored placeholder
and fixture arrangement are provided under CC0-1.0. This fixture verifies documented layout and
field normalization only. It does **not** satisfy Milestone 2's real-output fixture acceptance
criterion; a genuine run from a separate Python 3.10–3.12 Boltz environment is still required.
