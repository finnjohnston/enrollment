import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def valid_requirement_id():
    # Get a valid requirement ID from the first category of the first program
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    if not programs or not programs[0]["categories"] or not programs[0]["categories"][0]["requirements"]:
        pytest.skip("No requirements available for testing.")
    return programs[0]["categories"][0]["requirements"][0]["id"]


def test_get_requirement_valid(valid_requirement_id):
    response = client.get(f"/requirements/{valid_requirement_id}")
    assert response.status_code == 200
    req = response.json()
    assert req["id"] == valid_requirement_id
    assert "type" in req
    assert "data" in req


def test_get_requirement_invalid():
    response = client.get("/requirements/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Requirement not found" 