import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def plan_payload():
    # Get valid program IDs for plan creation
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    if not programs:
        pytest.skip("No programs available for planning.")
    return {
        "program_ids": [programs[0]["id"]],
        "start_semester": "Fall",
        "year": 2024
    }


def test_create_plan(plan_payload):
    response = client.post("/plans", json=plan_payload)
    assert response.status_code == 200
    plan = response.json()
    assert "id" in plan
    assert "programs" in plan
    assert "completed_courses" in plan
    assert "current_semester" in plan
    global created_plan_id
    created_plan_id = plan["id"]


def test_get_plan():
    response = client.get(f"/plans/{created_plan_id}")
    assert response.status_code == 200
    plan = response.json()
    assert plan["id"] == created_plan_id


def test_add_completed_course():
    # Get a course code from the catalog
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    if not courses:
        pytest.skip("No courses available to add.")
    course_code = courses[0]["course_code"]
    # Get program and category names from the created plan
    plan_resp = client.get(f"/plans/{created_plan_id}")
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    program = plan["programs"][0]
    program_name = program["name"]
    category_name = program["categories"][0]["category"]
    payload = {course_code: [(program_name, category_name)]}
    response = client.post(f"/plans/{created_plan_id}/add_completed_course", json=payload)
    assert response.status_code == 200
    plan = response.json()
    assert course_code in plan["completed_courses"]


def test_remove_completed_course():
    # Remove the course added in the previous test
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    if not courses:
        pytest.skip("No courses available to remove.")
    course_code = courses[0]["course_code"]
    response = client.post(f"/plans/{created_plan_id}/remove_completed_course", json={"course_code": course_code})
    assert response.status_code == 200
    plan = response.json()
    assert course_code not in plan["completed_courses"]


def test_advance_semester():
    response = client.post(f"/plans/{created_plan_id}/advance_semester")
    assert response.status_code == 200
    plan = response.json()
    assert "current_semester" in plan


def test_get_progress():
    response = client.get(f"/plans/{created_plan_id}/progress")
    assert response.status_code == 200
    plan = response.json()
    assert plan["id"] == created_plan_id


def test_invalid_plan_id():
    # Test all endpoints with an invalid plan ID
    invalid_id = 999999
    endpoints = [
        ("get", f"/plans/{invalid_id}"),
        ("post", f"/plans/{invalid_id}/add_completed_course", {"course_codes": ["FAKE101"]}),
        ("post", f"/plans/{invalid_id}/remove_completed_course", {"course_code": "FAKE101"}),
        ("post", f"/plans/{invalid_id}/advance_semester", None),
        ("get", f"/plans/{invalid_id}/progress")
    ]
    for method, url, *body in endpoints:
        if method == "get":
            resp = client.get(url)
        else:
            resp = client.post(url, json=body[0] if body else None)
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"] == "Plan not found" 