import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def created_plan_id():
    # Create a plan for testing recommendations
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    if not programs:
        pytest.skip("No programs available for planning.")
    payload = {
        "program_ids": [programs[0]["id"]],
        "start_semester": "Fall",
        "year": 2024
    }
    response = client.post("/plans", json=payload)
    assert response.status_code == 200
    plan = response.json()
    return plan["id"]


def test_get_recommendations_valid(created_plan_id):
    response = client.get(f"/plans/{created_plan_id}/recommendations")
    assert response.status_code == 200
    recs = response.json()
    assert "recommendations" in recs
    # Recommendations can be empty, but should be a dict or list
    assert isinstance(recs["recommendations"], (dict, list))


def test_get_recommendations_invalid():
    invalid_id = 999999
    response = client.get(f"/plans/{invalid_id}/recommendations")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Plan not found" 