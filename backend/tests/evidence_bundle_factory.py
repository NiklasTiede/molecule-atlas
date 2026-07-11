from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from warnings import catch_warnings, filterwarnings
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def evidence_bundle_bytes(
    source_root: Path,
    *,
    replacements: Mapping[str, bytes] | None = None,
    omitted: frozenset[str] = frozenset(),
    extra_members: tuple[tuple[str | ZipInfo, bytes], ...] = (),
) -> bytes:
    replacement_bytes = replacements or {}
    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(source_root.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(source_root).as_posix()
            if relative_path in omitted:
                continue
            archive.writestr(
                relative_path,
                replacement_bytes.get(relative_path, path.read_bytes()),
            )
        for name_or_info, contents in extra_members:
            with catch_warnings():
                filterwarnings("ignore", message="Duplicate name:", category=UserWarning)
                archive.writestr(name_or_info, contents)
    return output.getvalue()
