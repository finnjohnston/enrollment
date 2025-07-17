import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# --- Plan creation edge cases ---
def test_create_plan_empty_program_ids():
    payload = {"program_ids": [], "start_semester": "Fall", "year": 2024}
    resp = client.post("/plans", json=payload)
    # Should be valid (empty plan) or 422 depending on business logic
    assert resp.status_code in (200, 422)

def test_create_plan_min_year():
    payload = {"program_ids": [1], "start_semester": "Fall", "year": 0}
    resp = client.post("/plans", json=payload)
    assert resp.status_code in (200, 422)

def test_create_plan_max_year():
    payload = {"program_ids": [1], "start_semester": "Fall", "year": 9999}
    resp = client.post("/plans", json=payload)
    assert resp.status_code in (200, 422)

def test_create_plan_invalid_semester():
    payload = {"program_ids": [1], "start_semester": "NotASemester", "year": 2024}
    resp = client.post("/plans", json=payload)
    assert resp.status_code in (200, 422)

def test_create_plan_none_fields():
    payload = {"program_ids": None, "start_semester": None, "year": None}
    resp = client.post("/plans", json=payload)
    assert resp.status_code == 422

def test_create_plan_extreme_program_ids():
    payload = {"program_ids": [999999999], "start_semester": "Fall", "year": 2024}
    resp = client.post("/plans", json=payload)
    # Should be 200 with empty plan or 422/404 if program doesn't exist
    assert resp.status_code in (200, 422, 404)

# --- Non-existent IDs for plan/program/category/requirement ---
def test_get_nonexistent_plan():
    resp = client.get("/plans/99999999")
    assert resp.status_code == 404

def test_get_nonexistent_program():
    resp = client.get("/programs/99999999")
    assert resp.status_code == 404

def test_get_nonexistent_category():
    resp = client.get("/categories/99999999")
    assert resp.status_code == 404

def test_get_nonexistent_requirement():
    resp = client.get("/requirements/99999999")
    assert resp.status_code == 404 