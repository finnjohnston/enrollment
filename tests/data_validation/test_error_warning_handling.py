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

def test_plan_validation_error_on_unmet_prerequisites(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not category_name or not program_name:
        pytest.skip("No real course/category/program found for test.")
    # Add a real course to completed courses (simulate unmet prereqs)
    data = {course_code: [(program_name, category_name)]}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "errors" in result
    assert isinstance(result["errors"], list)
    # If plan is invalid, errors should be non-empty
    if not result["is_valid"]:
        assert result["errors"]

def test_plan_validation_warning_on_borderline(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    # Validate the plan as-is (should be valid, but may have warnings)
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "warnings" in result
    assert isinstance(result["warnings"], list)
    # If warnings exist, they should be non-empty strings
    if result["warnings"]:
        assert all(isinstance(w, str) and w for w in result["warnings"])

def test_plan_validation_error_structure(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    # Remove a course to make requirements impossible
    course_code = plan_and_metadata["course_code"]
    if not course_code:
        pytest.skip("No real course found for test.")
    client.post(f"/plans/{plan_id}/remove_completed_course", json={"course_code": course_code})
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert isinstance(result["errors"], list)
    # If plan is invalid, errors should be non-empty
    if not result["is_valid"]:
        assert result["errors"]

def test_plan_validation_warning_structure(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "warnings" in result
    assert isinstance(result["warnings"], list)
    # Warnings should be strings if present
    if result["warnings"]:
        assert all(isinstance(w, str) for w in result["warnings"]) 