import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def all_program_ids():
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    return [p["id"] for p in programs]

@pytest.fixture(scope="module")
def plan_id_single(all_program_ids):
    if not all_program_ids:
        pytest.skip("No programs available for planning.")
    payload = {
        "program_ids": [all_program_ids[0]],
        "start_semester": "Fall",
        "year": 2024
    }
    response = client.post("/plans", json=payload)
    assert response.status_code == 200
    return response.json()["id"]

@pytest.fixture(scope="module")
def plan_id_all(all_program_ids):
    if not all_program_ids:
        pytest.skip("No programs available for planning.")
    payload = {
        "program_ids": all_program_ids,
        "start_semester": "Fall",
        "year": 2024
    }
    response = client.post("/plans", json=payload)
    assert response.status_code == 200
    return response.json()["id"]

def test_plan_validation_single_program(benchmark, plan_id_single):
    def validate():
        response = client.post(f"/plans/{plan_id_single}/validate")
        assert response.status_code == 200
    benchmark(validate)

def test_plan_validation_all_programs(benchmark, plan_id_all):
    def validate():
        response = client.post(f"/plans/{plan_id_all}/validate")
        assert response.status_code == 200
    benchmark(validate) 