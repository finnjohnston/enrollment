import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def plan_and_metadata():
    # Create a valid plan and fetch real course, program, and category info
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    if not programs:
        pytest.skip("No programs available for planning.")
    program = programs[0]
    payload = {
        "program_ids": [program["id"]],
        "start_semester": "Fall",
        "year": 2024
    }
    response = client.post("/plans", json=payload)
    assert response.status_code == 200
    plan = response.json()
    # Get a real course code and category from the program
    course_code = None
    category_name = None
    program_name = program["name"]
    if program["categories"] and program["categories"][0]["requirements"]:
        category = program["categories"][0]
        category_name = category["category"]
        req = category["requirements"][0]
        data = req.get("data", {})
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], str):
                    course_code = v[0]
                    break
    if not course_code:
        courses_resp = client.get("/courses")
        if courses_resp.status_code == 200 and courses_resp.json():
            course_code = courses_resp.json()[0]["course_code"]
    return {
        "plan_id": plan["id"],
        "course_code": course_code,
        "category_name": category_name,
        "program_name": program_name
    }

# --- Impossible plan (remove all completed courses, try to validate) ---
def test_impossible_plan(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    if not course_code:
        pytest.skip("No real course found for test.")
    # Remove the real course from completed courses
    client.post(f"/plans/{plan_id}/remove_completed_course", json={"course_code": course_code})
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    # Should be invalid or have errors
    assert not result["is_valid"] or result["errors"]

# --- All requirements already satisfied (add all courses, validate) ---
def test_all_requirements_satisfied(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not program_name or not category_name:
        pytest.skip("No real course/category/program found for test.")
    # Add the real course to completed courses
    data = {course_code: [(program_name, category_name)]}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    # Should be valid or have only warnings
    assert result["is_valid"]

# --- Duplicate course assignments (add same course twice) ---
def test_duplicate_course_assignments(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not program_name or not category_name:
        pytest.skip("No real course/category/program found for test.")
    data = {course_code: [(program_name, category_name)]}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    # Should be valid or have warnings/errors about duplicates
    assert isinstance(result["is_valid"], bool)
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)

# --- Semester overflow (advance semester many times) ---
def test_semester_overflow(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    # Try to advance semester 20 times
    for _ in range(20):
        resp = client.post(f"/plans/{plan_id}/advance_semester")
        assert resp.status_code == 200
    # After many advances, plan should still be valid or have warnings
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result["is_valid"], bool)

# --- Semester underflow (no way to go back, but test get_progress at start) ---
def test_semester_underflow(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    # At the start, get progress should work
    resp = client.get(f"/plans/{plan_id}/progress")
    assert resp.status_code == 200
    result = resp.json()
    assert "current_semester" in result 