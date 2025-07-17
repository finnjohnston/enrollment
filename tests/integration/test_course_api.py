import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# Helper to get a valid course code from the catalog
@pytest.fixture(scope="module")
def valid_course_code():
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    if not courses:
        pytest.skip("No courses available in the catalog for testing.")
    return courses[0]["course_code"]


def test_list_courses():
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    assert isinstance(courses, list)
    # Optionally check for expected fields in the first course
    if courses:
        course = courses[0]
        assert "course_code" in course
        assert "title" in course
        assert "credits" in course


def test_get_course_valid(valid_course_code):
    response = client.get(f"/courses/{valid_course_code}")
    assert response.status_code == 200
    course = response.json()
    assert course["course_code"] == valid_course_code
    assert "title" in course
    assert "credits" in course


def test_get_course_invalid():
    response = client.get("/courses/INVALID_CODE_123")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Course not found" 