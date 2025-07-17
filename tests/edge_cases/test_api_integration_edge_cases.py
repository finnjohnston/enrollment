import pytest
from fastapi.testclient import TestClient
from api.main import app
import threading

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

# --- Concurrent plan modifications (simulate with threads) ---
def test_concurrent_plan_modifications(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not program_name or not category_name:
        pytest.skip("No real course/category/program found for test.")
    data = {course_code: [(program_name, category_name)]}
    def add_course():
        client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    def remove_course():
        client.post(f"/plans/{plan_id}/remove_completed_course", json={"course_code": course_code})
    threads = [threading.Thread(target=add_course), threading.Thread(target=remove_course)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Validate after concurrent modifications
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result

# --- Large batch operations (add/remove many courses) ---
def test_large_batch_operations(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    # Get a list of courses
    courses_resp = client.get("/courses")
    if courses_resp.status_code != 200 or not courses_resp.json():
        pytest.skip("No courses available for batch test.")
    courses = courses_resp.json()[:20]  # Limit to 20 for test
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not program_name or not category_name:
        pytest.skip("No real program/category found for test.")
    # Add many courses
    data = {c["course_code"]: [(program_name, category_name)] for c in courses}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    # Remove many courses
    for c in courses:
        client.post(f"/plans/{plan_id}/remove_completed_course", json={"course_code": c["course_code"]})
    # Validate after batch operations
    response = client.post(f"/plans/{plan_id}/validate")
    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result

# --- Cache edge cases (validate, add, remove, revalidate) ---
def test_cache_edge_cases(plan_and_metadata):
    plan_id = plan_and_metadata["plan_id"]
    course_code = plan_and_metadata["course_code"]
    program_name = plan_and_metadata["program_name"]
    category_name = plan_and_metadata["category_name"]
    if not course_code or not program_name or not category_name:
        pytest.skip("No real course/category/program found for test.")
    # Validate (should cache)
    response1 = client.post(f"/plans/{plan_id}/validate")
    assert response1.status_code == 200
    # Add course
    data = {course_code: [(program_name, category_name)]}
    client.post(f"/plans/{plan_id}/add_completed_course", json=data)
    # Validate again (should update cache)
    response2 = client.post(f"/plans/{plan_id}/validate")
    assert response2.status_code == 200
    # Remove course
    client.post(f"/plans/{plan_id}/remove_completed_course", json={"course_code": course_code})
    # Validate again (should update cache)
    response3 = client.post(f"/plans/{plan_id}/validate")
    assert response3.status_code == 200
    # All validations should return a valid structure
    for resp in [response1, response2, response3]:
        result = resp.json()
        assert "is_valid" in result 