from backend.app.main import app


def test_application_initialization():
    assert app.title == "AnalyzaX"
    assert app.version == "0.1.0"
    # Check that health route is mounted
    routes = [route.path for route in app.routes]
    assert "/api/v1/health" in routes
    assert "/" in routes
