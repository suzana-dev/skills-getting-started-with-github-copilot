import copy
import pytest
from urllib.parse import quote
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture()
def client():
    with TestClient(app, follow_redirects=False) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after every test."""
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index(client):
    response = client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_dict(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_contains_expected_fields(client):
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    url = f"/activities/{quote('Chess Club')}/signup?email=new@mergington.edu"
    response = client.post(url)
    assert response.status_code == 200
    assert "new@mergington.edu" in response.json()["message"]


def test_signup_participant_appears_in_activities(client):
    url = f"/activities/{quote('Chess Club')}/signup?email=new@mergington.edu"
    client.post(url)
    data = client.get("/activities").json()
    assert "new@mergington.edu" in data["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404(client):
    url = f"/activities/{quote('Unknown Activity')}/signup?email=x@mergington.edu"
    response = client.post(url)
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_duplicate_returns_400(client):
    url = f"/activities/{quote('Chess Club')}/signup?email=michael@mergington.edu"
    response = client.post(url)
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    url = f"/activities/{quote('Chess Club')}/signup?email=michael@mergington.edu"
    response = client.delete(url)
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]


def test_unregister_participant_removed_from_activities(client):
    url = f"/activities/{quote('Chess Club')}/signup?email=michael@mergington.edu"
    client.delete(url)
    data = client.get("/activities").json()
    assert "michael@mergington.edu" not in data["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404(client):
    url = f"/activities/{quote('Unknown Activity')}/signup?email=michael@mergington.edu"
    response = client.delete(url)
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_participant_not_found_returns_404(client):
    url = f"/activities/{quote('Chess Club')}/signup?email=nothere@mergington.edu"
    response = client.delete(url)
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]
