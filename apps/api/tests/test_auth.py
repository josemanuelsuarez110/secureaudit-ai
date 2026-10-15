"""Tests de autenticación."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """El endpoint /health responde 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_success(client: TestClient) -> None:
    """Registro exitoso devuelve 201 con user + token."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new_user@test.com",
            "password": "test_password_123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "new_user@test.com"
    assert data["user"]["full_name"] == "New User"
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient) -> None:
    """Registro con email duplicado devuelve 400."""
    payload = {
        "email": "duplicate@test.com",
        "password": "test_password_123",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "ya está registrado" in r2.json()["detail"]


def test_register_invalid_email(client: TestClient) -> None:
    """Registro con email inválido devuelve 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "test_password_123"},
    )
    assert response.status_code == 422


def test_register_short_password(client: TestClient) -> None:
    """Contraseña <8 caracteres devuelve 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "short@test.com", "password": "123"},
    )
    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    """Login con credenciales válidas devuelve token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@test.com", "password": "test_password_123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.com", "password": "test_password_123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    """Login con contraseña incorrecta devuelve 401."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@test.com", "password": "test_password_123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@test.com", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert "inválidas" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient) -> None:
    """Login con usuario inexistente devuelve 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "noexiste@test.com", "password": "test_password_123"},
    )
    assert response.status_code == 401
    assert "inválidas" in response.json()["detail"]


def test_me_without_token(client: TestClient) -> None:
    """/me sin token devuelve 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token(client: TestClient) -> None:
    """/me con token inválido devuelve 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert response.status_code == 401


def test_me_success(client: TestClient) -> None:
    """/me con token válido devuelve el usuario."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@test.com",
            "password": "test_password_123",
            "full_name": "Me User",
        },
    )
    token = r.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@test.com"
    assert data["full_name"] == "Me User"
