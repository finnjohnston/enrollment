import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def plan_id():
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
    return response.json()["id"]

def test_courses_response_time(benchmark):
    def get_courses():
        response = client.get("/courses")
        assert response.status_code == 200
    result = benchmark(get_courses)

def test_programs_response_time(benchmark):
    def get_programs():
        response = client.get("/programs")
        assert response.status_code == 200
    result = benchmark(get_programs)

def test_plan_create_response_time(benchmark):
    response = client.get("/programs")
    programs = response.json()
    payload = {
        "program_ids": [programs[0]["id"]],
        "start_semester": "Fall",
        "year": 2024
    }
    def create_plan():
        response = client.post("/plans", json=payload)
        assert response.status_code == 200
    result = benchmark(create_plan)

def test_plan_get_response_time(benchmark, plan_id):
    def get_plan():
        response = client.get(f"/plans/{plan_id}")
        assert response.status_code == 200
    result = benchmark(get_plan)

def test_recommendations_response_time(benchmark, plan_id):
    def get_recs():
        response = client.get(f"/plans/{plan_id}/recommendations")
        assert response.status_code == 200
    result = benchmark(get_recs)

def test_validation_response_time(benchmark, plan_id):
    def validate():
        response = client.post(f"/plans/{plan_id}/validate")
        assert response.status_code == 200
    result = benchmark(validate) 