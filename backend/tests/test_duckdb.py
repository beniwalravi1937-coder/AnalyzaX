from backend.app.services.duckdb_service import DuckDBService


def test_duckdb_initialization():
    service = DuckDBService()
    status = service.check_availability()
    assert status["status"] == "available"
    assert "version" in status


def test_duckdb_connection_context():
    service = DuckDBService()
    with service.get_connection() as conn:
        result = conn.execute("SELECT 100 + 42 AS total;").fetchone()
        assert result[0] == 142
