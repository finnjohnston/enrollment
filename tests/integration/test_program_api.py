import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def valid_program_id():
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    if not programs:
        pytest.skip("No programs available for testing.")
    return 0  # Use the first program's index


def test_list_programs():
    response = client.get("/programs")
    assert response.status_code == 200
    programs = response.json()
    assert isinstance(programs, list)
    if programs:
        program = programs[0]
        assert "id" in program
        assert "name" in program
        assert "categories" in program


def test_get_program_valid(valid_program_id):
    response = client.get(f"/programs/{valid_program_id}")
    assert response.status_code == 200
    program = response.json()
    assert program["id"] == valid_program_id
    assert "name" in program
    assert "categories" in program


def test_get_program_invalid():
    response = client.get("/programs/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Program not found"


def test_list_program_categories_valid(valid_program_id):
    response = client.get(f"/programs/{valid_program_id}/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    if categories:
        category = categories[0]
        assert "id" in category
        assert "category" in category
        assert "requirements" in category


def test_list_program_categories_invalid():
    response = client.get("/programs/999999/categories")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Program not found" 