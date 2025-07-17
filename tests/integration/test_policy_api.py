import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_list_policies():
    response = client.get("/policies")
    assert response.status_code == 200
    policies = response.json()
    assert isinstance(policies, list)
    if policies:
        assert "name" in policies[0] or "description" in policies[0] or isinstance(policies[0], dict)


def test_get_policy_valid():
    response = client.get("/policies")
    assert response.status_code == 200
    policies = response.json()
    if not policies:
        pytest.skip("No policies available for testing.")
    response = client.get(f"/policies/0")
    assert response.status_code == 200
    policy = response.json()
    assert isinstance(policy, dict)
    # Optionally check for expected fields
    assert "name" in policy or "description" in policy or len(policy) > 0


def test_get_policy_invalid():
    response = client.get("/policies/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Policy not found" 