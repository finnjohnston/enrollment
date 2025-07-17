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


def test_plan_creation_single_program(benchmark, all_program_ids):
    if not all_program_ids:
        pytest.skip("No programs available for planning.")
    payload = {
        "program_ids": [all_program_ids[0]],
        "start_semester": "Fall",
        "year": 2024
    }
    def create_plan():
        response = client.post("/plans", json=payload)
        assert response.status_code == 200
    benchmark(create_plan)


def test_plan_creation_all_programs(benchmark, all_program_ids):
    if not all_program_ids:
        pytest.skip("No programs available for planning.")
    payload = {
        "program_ids": all_program_ids,
        "start_semester": "Fall",
        "year": 2024
    }
    def create_plan():
        response = client.post("/plans", json=payload)
        assert response.status_code == 200
    benchmark(create_plan) 