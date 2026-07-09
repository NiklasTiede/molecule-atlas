import json
from pathlib import Path

from app.main import app

OPENAPI_PATH = Path(__file__).parents[2] / "frontend" / "openapi.json"


def test_checked_in_openapi_schema_matches_application() -> None:
    checked_in_schema = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))

    assert checked_in_schema == app.openapi()
