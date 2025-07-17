import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def valid_category_id():
    # Get a valid category ID from the first program
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    if not programs or not programs[0]["categories"]:
        pytest.skip("No categories available for testing.")
    return programs[0]["categories"][0]["id"]


def test_get_category_valid(valid_category_id):
    response = client.get(f"/categories/{valid_category_id}")
    assert response.status_code == 200
    category = response.json()
    assert category["id"] == valid_category_id
    assert "category" in category
    assert "requirements" in category


def test_get_category_invalid():
    response = client.get("/categories/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Category not found"


def test_list_category_requirements_valid(valid_category_id):
    response = client.get(f"/categories/{valid_category_id}/requirements")
    assert response.status_code == 200
    requirements = response.json()
    assert isinstance(requirements, list)
    # Optionally check for expected fields in the first requirement
    if requirements:
        req = requirements[0]
        assert "id" in req
        assert "type" in req
        assert "data" in req


def test_list_category_requirements_invalid():
    response = client.get("/categories/999999/requirements")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Category not found" 