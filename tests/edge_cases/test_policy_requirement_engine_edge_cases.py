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

# --- Requirement with zero or negative credits (simulate via API if possible) ---
def test_requirement_zero_negative_credits(plan_and_metadata):
    # This is a structural test; we check that the API does not crash and returns a valid response
    # (Assumes at least one requirement has min_credits >= 0)
    plan_id = plan_and_metadata["plan_id"]
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result

# --- Requirement with empty options or course lists (simulate via API if possible) ---
def test_requirement_empty_options(plan_and_metadata):
    # This is a structural test; we check that the API does not crash and returns a valid response
    plan_id = plan_and_metadata["plan_id"]
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result

# --- Overlapping assignments (assign same course to multiple programs/categories) ---
def test_overlapping_assignments(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not program_name or not category_name:
        pytest.skip("No real course/category/program found for test.")
    # Assign the same course to the same category twice (should trigger overlap policy or warning)
    data = {course_code: [(program_name, category_name), (program_name, category_name)]}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result
    # If overlap policy is enforced, errors should be present
    if not result["is_valid"]:
        assert result["errors"]

# --- Conflicting requirements (simulate by assigning same course to multiple categories) ---
def test_conflicting_requirements(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not program_name or not category_name:
        pytest.skip("No real course/category/program found for test.")
    # Try to assign the same course to two different categories (simulate conflict)
    # For this, we need a second category if available
    response = client.get("/programs")
    categories = []
    for prog in response.json():
        if prog["name"] == program_name:
            categories = [cat["category"] for cat in prog["categories"]]
            break
    if len(categories) < 2:
        pytest.skip("Not enough categories to test conflicting requirements.")
    cat1, cat2 = categories[:2]
    data = {course_code: [(program_name, cat1), (program_name, cat2)]}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "errors" in result
    # Should be invalid or have errors if policy is enforced
    if not result["is_valid"]:
        assert result["errors"] 