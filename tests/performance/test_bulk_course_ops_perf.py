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

@pytest.fixture(scope="module")
def many_course_codes():
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    # Use up to 100 courses for bulk testing
    return [c["course_code"] for c in courses[:100]]

def test_bulk_add_completed_courses(benchmark, plan_id, many_course_codes):
    # Get program and category names from the plan
    plan_resp = client.get(f"/plans/{plan_id}")
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    program = plan["programs"][0]
    program_name = program["name"]
    category_name = program["categories"][0]["category"]
    payload = {code: [(program_name, category_name)] for code in many_course_codes}
    def add_courses():
        response = client.post(f"/plans/{plan_id}/add_completed_course", json=payload)
        assert response.status_code == 200
    benchmark(add_courses)

def test_bulk_remove_completed_courses(benchmark, plan_id, many_course_codes):
    def remove_courses():
        for code in many_course_codes:
            response = client.post(f"/plans/{plan_id}/remove_completed_course", json={"course_code": code})
            assert response.status_code == 200
    benchmark(remove_courses) 