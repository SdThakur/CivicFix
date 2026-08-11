"""API integration tests for Authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """Test user registration endpoint."""
    payload = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "New User",
        "role": "CITIZEN",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_user_registration_fails(client: AsyncClient):
    """Test registering with an existing email returns HTTP 400."""
    payload = {
        "email": "dup@example.com",
        "password": "securepassword123",
        "full_name": "Dup User",
    }
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test login with valid credentials returns JWT token."""
    reg_payload = {
        "email": "loginuser@example.com",
        "password": "password123",
        "full_name": "Login User",
    }
    await client.post("/auth/register", json=reg_payload)

    login_payload = {
        "email": "loginuser@example.com",
        "password": "password123",
    }
    response = await client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password returns 401 Unauthorized."""
    reg_payload = {
        "email": "userpass@example.com",
        "password": "correctpassword",
        "full_name": "User Pass",
    }
    await client.post("/auth/register", json=reg_payload)

    login_payload = {
        "email": "userpass@example.com",
        "password": "wrongpassword",
    }
    response = await client.post("/auth/login", json=login_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, citizen_token_headers: dict):
    """Test getting current user profile with token header."""
    response = await client.get("/auth/me", headers=citizen_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "citizen@example.com"
