from pra.api import ScanRequest, create_app


def test_health():
    app = create_app()
    route = next(route for route in app.routes if getattr(route, "path", None) == "/health")

    assert route.endpoint() == {"status": "ok"}


def test_scan_endpoint(tmp_path):
    kb = tmp_path / "kb.yaml"
    kb.write_text("pattern: system.heartbeat_repeated_check\n", encoding="utf-8")
    app = create_app()
    route = next(route for route in app.routes if getattr(route, "path", None) == "/scan")

    body = route.endpoint(ScanRequest(path=str(kb)))

    assert body["summary"]["patterns_found"] == 1
