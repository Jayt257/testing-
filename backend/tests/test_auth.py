"""
backend/tests/test_auth.py
Auth endpoint tests: register, login, get profile, token validation.
"""
import pytest


def test_register_new_user(client):
    resp = client.post("/api/auth/register", json={
        "username": "newlearner",
        "email": "newlearner@test.com",
        "password": "NewPass@123",
        "native_lang": "hi",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # Register returns {access_token, token_type, user}
    assert "user" in data
    assert data["user"]["email"] == "newlearner@test.com"
    assert data["user"]["role"] == "user"


def test_register_duplicate_email(client):
    payload = {"username": "dup1", "email": "dup@test.com", "password": "Pass@123", "native_lang": "hi"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code in (400, 409)


def test_login_success(client, regular_user):
    resp = client.post("/api/auth/login", json={"email": "user@test.com", "password": "Test@1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, regular_user):
    resp = client.post("/api/auth/login", json={"email": "user@test.com", "password": "WrongPass"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={"email": "ghost@test.com", "password": "anything"})
    assert resp.status_code == 401


def test_get_profile(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "user@test.com"
    assert data["role"] == "user"


def test_get_profile_no_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


def test_get_profile_bad_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code in (401, 403)


def test_schema_username_length(client):
    resp = client.post("/api/auth/register", json={
        "username": "ab",
        "email": "short@test.com",
        "password": "ValidPassword123",
    })
    assert resp.status_code == 422


def test_schema_username_chars(client):
    resp = client.post("/api/auth/register", json={
        "username": "bad username!",
        "email": "badchar@test.com",
        "password": "ValidPassword123",
    })
    assert resp.status_code == 422


def test_schema_password_length(client):
    resp = client.post("/api/auth/register", json={
        "username": "gooduser",
        "email": "weakpass@test.com",
        "password": "short",
    })
    assert resp.status_code == 422


def test_register_duplicate_username(client):
    # Already created newlearner in test_register_new_user, but the DB is rolled back or cleared?
    # Let's create one explicitly then duplicate it
    payload1 = {"username": "unique1", "email": "unique1@test.com", "password": "Pass@123", "native_lang": "hi"}
    client.post("/api/auth/register", json=payload1)
    # Give it a different email but same username
    payload2 = {"username": "unique1", "email": "unique2@test.com", "password": "Pass@123", "native_lang": "hi"}
    resp = client.post("/api/auth/register", json=payload2)
    assert resp.status_code == 400
    assert "Username already taken" in resp.text


def test_login_inactive_user(client, db):
    # Create an inactive user manually in the DB
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    u = User(username="inactive", email="inactivelogin@test.com", password_hash=hash_password("Pass123"), role=UserRole.user, is_active=False)
    db.add(u)
    db.commit()
    
    resp = client.post("/api/auth/login", json={"email": "inactivelogin@test.com", "password": "Pass123"})
    assert resp.status_code == 403
    assert "deactivated" in resp.text


def test_admin_login_success(client, admin_user):
    resp = client.post("/api/auth/admin/login", json={"email": "admin@test.com", "password": "Admin@1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_admin_login_invalid(client, admin_user):
    resp = client.post("/api/auth/admin/login", json={"email": "admin@test.com", "password": "WrongPassword"})
    assert resp.status_code == 401
    assert "Invalid admin credentials" in resp.text

    resp2 = client.post("/api/auth/admin/login", json={"email": "notadmin@test.com", "password": "Admin@1234"})
    assert resp2.status_code == 401

