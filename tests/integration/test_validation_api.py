import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def created_plan_id():
    # Create a plan for testing validation
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


def test_validate_plan_valid(created_plan_id):
    response = client.post(f"/plans/{created_plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result


def test_validate_semester_valid(created_plan_id):
    response = client.post(f"/plans/{created_plan_id}/validate_semester")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result


def test_validate_assignment_valid(created_plan_id):
    response = client.post(f"/plans/{created_plan_id}/validate_assignment")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result


def test_validate_invalid_plan():
    invalid_id = 999999
    endpoints = [
        f"/plans/{invalid_id}/validate",
        f"/plans/{invalid_id}/validate_semester",
        f"/plans/{invalid_id}/validate_assignment"
    ]
    for url in endpoints:
        resp = client.post(url)
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"] == "Plan not found" 