"""Tests de organizaciones (CRUD)."""

from fastapi.testclient import TestClient


def _register_user(
    client: TestClient,
    email: str = "test@empresa.com",
    with_org: bool = True,
) -> dict:
    """Helper: registra usuario y devuelve token + datos."""
    payload = {
        "email": email,
        "password": "test_password_123",
        "full_name": "Test User",
    }
    if with_org:
        payload["organization_name"] = f"Org de {email}"
        payload["organization_slug"] = email.split("@")[0].replace(".", "-") + "-org"

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# Listar
# =========================================================

def test_list_organizations_empty(client: TestClient) -> None:
    """Usuario sin organizaciones ve lista vacía."""
    data = _register_user(client, "no-org@test.com", with_org=False)
    headers = _auth_headers(data["access_token"])

    response = client.get("/api/v1/organizations", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_organizations_one(client: TestClient) -> None:
    """Usuario con 1 organización la ve."""
    data = _register_user(client, "one@test.com", with_org=True)
    headers = _auth_headers(data["access_token"])

    response = client.get("/api/v1/organizations", headers=headers)
    assert response.status_code == 200
    orgs = response.json()
    assert len(orgs) == 1
    assert orgs[0]["slug"] == "one-org"


def test_list_organizations_requires_auth(client: TestClient) -> None:
    """Sin token → 401."""
    response = client.get("/api/v1/organizations")
    assert response.status_code == 401


# =========================================================
# Crear
# =========================================================

def test_create_organization(client: TestClient) -> None:
    """Usuario autenticado puede crear organización adicional."""
    data = _register_user(client, "creator@test.com", with_org=False)
    headers = _auth_headers(data["access_token"])

    response = client.post(
        "/api/v1/organizations",
        json={"name": "Nueva Org", "slug": "nueva-org"},
        headers=headers,
    )
    assert response.status_code == 201
    org = response.json()
    assert org["name"] == "Nueva Org"
    assert org["slug"] == "nueva-org"

    # Verificar que ahora la ve
    list_response = client.get("/api/v1/organizations", headers=headers)
    assert len(list_response.json()) == 1


def test_create_organization_duplicate_slug(client: TestClient) -> None:
    """Slug duplicado → 400."""
    data1 = _register_user(client, "first@test.com", with_org=False)
    headers1 = _auth_headers(data1["access_token"])
    client.post(
        "/api/v1/organizations",
        json={"name": "Org 1", "slug": "slug-dup"},
        headers=headers1,
    )

    # Segundo usuario intenta con el mismo slug
    data2 = _register_user(client, "second@test.com", with_org=False)
    headers2 = _auth_headers(data2["access_token"])
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Org 2", "slug": "slug-dup"},
        headers=headers2,
    )
    assert response.status_code == 400
    assert "slug" in response.json()["detail"].lower()


def test_create_organization_invalid_slug(client: TestClient) -> None:
    """Slug inválido → 422."""
    data = _register_user(client, "invalid@test.com", with_org=False)
    headers = _auth_headers(data["access_token"])

    response = client.post(
        "/api/v1/organizations",
        json={"name": "Org", "slug": "INVALID SLUG!"},
        headers=headers,
    )
    assert response.status_code == 422


# =========================================================
# Ver
# =========================================================

def test_get_organization(client: TestClient) -> None:
    """Usuario puede ver su propia organización."""
    data = _register_user(client, "get@test.com", with_org=True)
    headers = _auth_headers(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.get(f"/api/v1/organizations/{org_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == org_id


def test_get_organization_not_member(client: TestClient) -> None:
    """Usuario no puede ver una organización de la que no es miembro → 404."""
    # Usuario A con org
    data_a = _register_user(client, "user-a@test.com", with_org=True)
    org_a_id = data_a["organization"]["id"]

    # Usuario B sin esa org
    data_b = _register_user(client, "user-b@test.com", with_org=False)
    headers_b = _auth_headers(data_b["access_token"])

    response = client.get(
        f"/api/v1/organizations/{org_a_id}",
        headers=headers_b,
    )
    assert response.status_code == 404


# =========================================================
# Actualizar
# =========================================================

def test_update_organization(client: TestClient) -> None:
    """Admin puede actualizar su organización."""
    data = _register_user(client, "update@test.com", with_org=True)
    headers = _auth_headers(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Nuevo Nombre"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Nuevo Nombre"


def test_update_organization_not_member(client: TestClient) -> None:
    """Usuario sin acceso → 403."""
    data_a = _register_user(client, "a-update@test.com", with_org=True)
    org_a_id = data_a["organization"]["id"]

    data_b = _register_user(client, "b-update@test.com", with_org=False)
    headers_b = _auth_headers(data_b["access_token"])

    response = client.patch(
        f"/api/v1/organizations/{org_a_id}",
        json={"name": "Hackeado"},
        headers=headers_b,
    )
    assert response.status_code == 403


# =========================================================
# Eliminar
# =========================================================

def test_delete_organization(client: TestClient) -> None:
    """Admin puede eliminar su organización."""
    data = _register_user(client, "delete@test.com", with_org=True)
    headers = _auth_headers(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.delete(f"/api/v1/organizations/{org_id}", headers=headers)
    assert response.status_code == 204

    # Ya no aparece en la lista
    list_response = client.get("/api/v1/organizations", headers=headers)
    assert len(list_response.json()) == 0


def test_delete_organization_not_member(client: TestClient) -> None:
    """Usuario sin acceso → 403."""
    data_a = _register_user(client, "a-del@test.com", with_org=True)
    org_a_id = data_a["organization"]["id"]

    data_b = _register_user(client, "b-del@test.com", with_org=False)
    headers_b = _auth_headers(data_b["access_token"])

    response = client.delete(
        f"/api/v1/organizations/{org_a_id}",
        headers=headers_b,
    )
    assert response.status_code == 403
