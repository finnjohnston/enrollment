from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_get_negative_plan():
    resp = client.get("/plans/-1")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Plan not found"

def test_get_negative_program():
    resp = client.get("/programs/-1")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Program not found"

def test_get_negative_category():
    resp = client.get("/categories/-1")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Category not found"

def test_get_negative_requirement():
    resp = client.get("/requirements/-1")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Requirement not found"

def test_post_negative_plan_validate():
    resp = client.post("/plans/-1/validate")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Plan not found"

def test_post_negative_plan_validate_semester():
    resp = client.post("/plans/-1/validate_semester")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Plan not found"

def test_post_negative_plan_validate_assignment():
    resp = client.post("/plans/-1/validate_assignment")
    assert resp.status_code in (404, 422)
    if resp.status_code == 404:
        assert resp.json().get("detail") == "Plan not found" 