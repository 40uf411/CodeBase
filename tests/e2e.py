# tests/e2e.py
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from uuid import UUID
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

ADMIN_EMAIL = "t@t.com"
ADMIN_FULL_NAME = "Initial Admin"
# we leave ADMIN_PASSWORD None so bootstrap generates one for us

@pytest.fixture(scope="session")
def admin_token():
    # 1) Bootstrap the first superuser
    rv = client.post(
        "/api/v1/auth/bootstrap",
        json={"email": ADMIN_EMAIL, "full_name": ADMIN_FULL_NAME},
    )
    assert rv.status_code == 201, rv.text
    creds = rv.json()
    assert creds["email"] == ADMIN_EMAIL
    assert "password" in creds and len(creds["password"]) >= 16

    # 2) Log in as that superuser
    rv = client.post(
        "/api/v1/auth/login",
        data={"username": ADMIN_EMAIL, "password": creds["password"]},
    )
    assert rv.status_code == 200, rv.text
    tok = rv.json()
    assert "access_token" in tok and "refresh_token" in tok
    return tok["access_token"]

def test_cannot_bootstrap_twice(admin_token):
    # Attempt to bootstrap again -> 400
    rv = client.post(
        "/api/v1/auth/bootstrap",
        json={"email": "hacker@example.com"}
    )
    assert rv.status_code == 400
    assert "already set up" in rv.json()["detail"]

def test_admin_can_CRUD_privileges_and_roles(admin_token):
    h = {"Authorization": f"Bearer {admin_token}"}

    # CREATE a privilege
    priv_payload = {"name": "demo:read", "description": "demo read"}
    rv = client.post("/api/v1/privileges/", headers=h, json=priv_payload)
    assert rv.status_code == 201, rv.text
    priv = rv.json()
    assert priv["name"] == "demo:read"

    # READ it back
    rv = client.get(f"/api/v1/privileges/{priv['id']}", headers=h)
    assert rv.status_code == 200
    assert rv.json()["name"] == "demo:read"

    # UPDATE it
    rv = client.put(
        f"/api/v1/privileges/{priv['id']}",
        headers=h,
        json={"description": "updated desc"},
    )
    assert rv.status_code == 200
    assert rv.json()["description"] == "updated desc"

    # DELETE it
    rv = client.delete(f"/api/v1/privileges/{priv['id']}", headers=h)
    assert rv.status_code == 200
    # subsequent GET should 404
    rv = client.get(f"/api/v1/privileges/{priv['id']}", headers=h)
    assert rv.status_code == 404

    # Now do the same for roles
    role_payload = {"name": "demo_role", "description": "a test role"}
    rv = client.post("/api/v1/roles/", headers=h, json=role_payload)
    assert rv.status_code == 201
    role = rv.json()
    assert role["name"] == "demo_role"

    rv = client.get(f"/api/v1/roles/{role['id']}", headers=h)
    assert rv.status_code == 200
    assert rv.json()["name"] == "demo_role"

    rv = client.put(
        f"/api/v1/roles/{role['id']}",
        headers=h,
        json={"description": "updated role"},
    )
    assert rv.status_code == 200
    assert rv.json()["description"] == "updated role"

    rv = client.delete(f"/api/v1/roles/{role['id']}", headers=h)
    assert rv.status_code == 200
    rv = client.get(f"/api/v1/roles/{role['id']}", headers=h)
    assert rv.status_code == 404

@pytest.fixture
def normal_user_token(admin_token):
    # As admin, REGISTER a normal user
    h = {"Authorization": f"Bearer {admin_token}"}
    new_user = {
        "email": "joe@example.com",
        "password": "secret123",
        "full_name": "Joe Normal"
    }
    rv = client.post("/api/v1/auth/register", json=new_user)
    assert rv.status_code == 201, rv.text

    # Login as that user
    rv = client.post(
        "/api/v1/auth/login",
        data={"username": new_user["email"], "password": new_user["password"]},
    )
    assert rv.status_code == 200, rv.text
    return rv.json()["access_token"]

def test_normal_user_cannot_manage_privileges(normal_user_token):
    h = {"Authorization": f"Bearer {normal_user_token}"}
    rv = client.post("/api/v1/privileges/", headers=h, json={"name":"x:y"})
    assert rv.status_code == 403

def test_normal_user_cannot_manage_roles(normal_user_token):
    h = {"Authorization": f"Bearer {normal_user_token}"}
    rv = client.post("/api/v1/roles/", headers=h, json={"name":"r","description":""})
    assert rv.status_code == 403

def test_grant_and_use_privileges(admin_token, normal_user_token):
    ah = {"Authorization": f"Bearer {admin_token}"}

    # 1) Ensure CRUD-privileges exist for role entity
    rv = client.post("/api/v1/privileges/entity/role/crud", headers=ah)
    assert rv.status_code == 200
    privs = {p["name"]: p["id"] for p in rv.json()}

    # 2) Create a “priv_manager” role
    rv = client.post(
        "/api/v1/roles/",
        headers=ah,
        json={"name":"priv_manager","description":"can manage privs"}
    )
    role = rv.json()

    # 3) ASSIGN all role‐related privileges into priv_manager
    for name, pid in privs.items():
        rv = client.post(
            f"/api/v1/privileges/{pid}/assign-to-role/{role['id']}",
            headers=ah
        )
        assert rv.status_code == 200

    # 4) Now _assign_ the normal user into that role.
    #    (Assuming you have an endpoint like /roles/{role_id}/assign/{user_id}.)
    rv = client.post(f"/api/v1/roles/{role['id']}/assign/{UUID(normal_user_token)}", headers=ah)
    # if your route differs, adjust accordingly:
    assert rv.status_code in (200, 204)

    # 5) Now normal user can create privileges
    nh = {"Authorization": f"Bearer {normal_user_token}"}
    rv = client.post("/api/v1/privileges/", headers=nh, json={"name":"foo:bar"})
    assert rv.status_code == 201
    assert rv.json()["name"] == "foo:bar"

    # ...and so on for update/delete.

