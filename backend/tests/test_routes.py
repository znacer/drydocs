"""Tests for API routes."""

from uuid import uuid4


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Document Manager API"
    assert data["version"] == "1.0.0"


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_documents_empty(client):
    """Test listing documents when none exist."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["documents"] == []


def test_get_nonexistent_document(client):
    """Test getting a non-existent document."""
    response = client.get(f"/documents/{uuid4()}")
    assert response.status_code == 404


def test_delete_nonexistent_document(client):
    """Test deleting a non-existent document."""
    response = client.delete(f"/documents/{uuid4()}")
    assert response.status_code == 404


def test_search_endpoint(client):
    """Test the search endpoint."""
    response = client.post(
        "/search",
        json={"query": "test", "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert "total" in data


def test_search_invalid_query(client):
    """Test search with invalid query."""
    response = client.post(
        "/search",
        json={"query": "", "limit": 10, "offset": 0},  # Empty query
    )
    # Should fail validation since query has min_length=1
    assert response.status_code == 422


def test_get_references_nonexistent(client):
    """Test getting references for a non-existent document."""
    response = client.get(f"/documents/{uuid4()}/references")
    assert response.status_code == 404


def test_get_outgoing_references_nonexistent(client):
    """Test getting outgoing references for a non-existent document."""
    response = client.get(f"/documents/{uuid4()}/references/outgoing")
    assert response.status_code == 404


def test_get_incoming_references_nonexistent(client):
    """Test getting incoming references for a non-existent document."""
    response = client.get(f"/documents/{uuid4()}/references/incoming")
    assert response.status_code == 404


def test_validate_nonexistent_document(client):
    """Test validating a non-existent document."""
    response = client.post(
        f"/documents/{uuid4()}/validate",
        json={"user_id": str(uuid4()), "notes": "Test"},
    )
    assert response.status_code == 404
