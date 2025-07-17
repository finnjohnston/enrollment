import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# --- /plans (PlanCreateSchema) ---
def test_create_plan_missing_required():
    # Missing program_ids
    payload = {'start_semester': 'Fall', 'year': 2024}
    resp = client.post('/plans', json=payload)
    assert resp.status_code == 422
    # Missing start_semester
    payload = {'program_ids': [1], 'year': 2024}
    resp = client.post('/plans', json=payload)
    assert resp.status_code == 422
    # Missing year
    payload = {'program_ids': [1], 'start_semester': 'Fall'}
    resp = client.post('/plans', json=payload)
    assert resp.status_code == 422

def test_create_plan_wrong_type():
    # program_ids should be a list
    payload = {'program_ids': 'notalist', 'start_semester': 'Fall', 'year': 2024}
    resp = client.post('/plans', json=payload)
    assert resp.status_code == 422
    # year should be int
    payload = {'program_ids': [1], 'start_semester': 'Fall', 'year': 'notanint'}
    resp = client.post('/plans', json=payload)
    assert resp.status_code == 422

# --- /plans/{plan_id}/add_completed_course ---
def test_add_completed_course_missing_body():
    # Should require a body
    resp = client.post('/plans/1/add_completed_course')
    assert resp.status_code == 422

def test_add_completed_course_wrong_type():
    # Should be dict of str to list
    resp = client.post('/plans/1/add_completed_course', json=[1,2,3])
    assert resp.status_code == 422

# --- /plans/{plan_id}/remove_completed_course ---
def test_remove_completed_course_missing_body():
    resp = client.post('/plans/1/remove_completed_course')
    assert resp.status_code == 422

def test_remove_completed_course_wrong_type():
    resp = client.post('/plans/1/remove_completed_course', json=[1,2,3])
    assert resp.status_code == 422

# --- /plans/{plan_id}/validate, /validate_semester, /validate_assignment ---
def test_validation_endpoints_invalid_plan():
    invalid_id = 999999
    endpoints = [
        f'/plans/{invalid_id}/validate',
        f'/plans/{invalid_id}/validate_semester',
        f'/plans/{invalid_id}/validate_assignment'
    ]
    for url in endpoints:
        resp = client.post(url)
        assert resp.status_code == 404
        data = resp.json()
        assert data['detail'] == 'Plan not found' 