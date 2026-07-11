from collections.abc import Mapping

from httpx2 import Response

class TestClient:
    def __init__(self, app: object) -> None: ...
    def get(self, url: str, *, headers: Mapping[str, str] | None = None) -> Response: ...
    def post(
        self,
        url: str,
        *,
        files: object | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response: ...
