# PoseBusters 0.6.5 `mol` full-report fixture

This is genuine PoseBusters validator output over a synthetic CC0 molecule. It is computational
validation evidence, not a claim about a real ligand, pose, protein, or biological activity.

- Upstream repository: <https://github.com/maabuu/posebusters>
- Upstream release: `v0.6.5`
- Upstream release commit: `1a5f26aa7270fafba21b7fec8b3633f4c4e45ead`
- Upstream license: MIT
- Capture date: 2026-07-11
- Configuration: built-in `mol`
- `full_report`: `True`
- Parallel workers: `0`
- Python: `3.13.13`
- Platform: Darwin arm64, CPU
- PoseBusters: `0.6.5`
- RDKit: `2026.3.3`
- pandas: `3.0.3`
- NumPy: `2.5.0`

The input is copied from Molecule Atlas's manually authored successful evidence fixture and is
provided under CC0-1.0. The raw CSV is the unmodified `DataFrame.to_csv(index=True,
lineterminator="\\n")` result, apart from excluding PoseBusters/RDKit's stderr warning that the input
was tagged 2D while containing a nonzero Z coordinate.

Capture command, executed from a temporary directory containing `predicted-pose.sdf`:

```bash
uv run --python /path/to/python3.13 --with "posebusters==0.6.5" python -c \
  'from posebusters import PoseBusters; p="predicted-pose.sdf"; print(PoseBusters(config="mol", max_workers=0).bust(p, full_report=True).to_csv(index=True, lineterminator="\n"))'
```

The numeric energy fields are retained as raw upstream output. They are not experimental energies,
affinities, or a Molecule Atlas ranking score.
