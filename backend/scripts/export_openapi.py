import json
from pathlib import Path

from app.main import app

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def main() -> None:
    schema = json.dumps(app.openapi(), indent=2, sort_keys=True)
    OPENAPI_PATH.write_text(f"{schema}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
