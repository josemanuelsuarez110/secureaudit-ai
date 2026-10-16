"""Tests de assets (dominios)."""

from fastapi.testclient import TestClient


def _register_with_org(
    client: TestClient,
    email: str = "user@test.com",
    org_slug: str = "user-org",
) -> dict:
    """Helper: registra usuario + organización."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "test_password_123",
            "full_name": "Test User",
            "organization_name": f"Org de {email}",
            "organization_slug": org_slug,
        },
    )
    assert response.status_code == 201
    return response.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# Listar assets
# =========================================================

def test_list_assets_empty(client: TestClient) -> None:
    """Usuario con org sin assets ve lista vacía."""
    data = _register_with_org(client, "empty@test.com", "empty-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.get(
        f"/api/v1/assets/organizations/{org_id}/assets",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_assets_requires_auth(client: TestClient) -> None:
    """Sin token → 401."""
    data = _register_with_org(client, "noauth@test.com", "noauth-org")
    org_id = data["organization"]["id"]

    response = client.get(f"/api/v1/assets/organizations/{org_id}/assets")
    assert response.status_code == 401


def test_list_assets_not_member(client: TestClient) -> None:
    """Usuario no miembro no puede listar → 403."""
    # Usuario A con org
    data_a = _register_with_org(client, "user-a@test.com", "user-a-org")
    org_a_id = data_a["organization"]["id"]

    # Usuario B sin esa org
    data_b = _register_with_org(client, "user-b@test.com", "user-b-org")
    headers_b = _auth(data_b["access_token"])

    response = client.get(
        f"/api/v1/assets/organizations/{org_a_id}/assets",
        headers=headers_b,
    )
    assert response.status_code == 403


# =========================================================
# Crear assets
# =========================================================

def test_create_asset(client: TestClient) -> None:
    """Miembro puede crear asset."""
    data = _register_with_org(client, "create@test.com", "create-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={
            "domain": "ejemplo.com",
            "display_name": "Mi sitio principal",
        },
        headers=headers,
    )
    assert response.status_code == 201
    asset = response.json()
    assert asset["domain"] == "ejemplo.com"
    assert asset["display_name"] == "Mi sitio principal"
    assert asset["status"] == "pending_verification"
    assert asset["organization_id"] == org_id
    assert "verification_token" in asset
    assert len(asset["verification_token"]) > 20


def test_create_asset_duplicate_domain(client: TestClient) -> None:
    """Dominio duplicado en la misma org → 400."""
    data = _register_with_org(client, "dup@test.com", "dup-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    payload = {"domain": "duplicado.com"}

    r1 = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json=payload,
        headers=headers,
    )
    assert r1.status_code == 201

    r2 = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json=payload,
        headers=headers,
    )
    assert r2.status_code == 400
    assert "dominio" in r2.json()["detail"].lower()


def test_create_asset_invalid_domain(client: TestClient) -> None:
    """Dominio inválido → 422."""
    data = _register_with_org(client, "invalid@test.com", "invalid-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": "not a domain!"},
        headers=headers,
    )
    assert response.status_code == 422


def test_create_asset_not_member(client: TestClient) -> None:
    """Usuario no miembro no puede crear → 400."""
    # Usuario A con org
    data_a = _register_with_org(client, "a-create@test.com", "a-create-org")
    org_a_id = data_a["organization"]["id"]

    # Usuario B
    data_b = _register_with_org(client, "b-create@test.com", "b-create-org")
    headers_b = _auth(data_b["access_token"])

    response = client.post(
        f"/api/v1/assets/organizations/{org_a_id}/assets",
        json={"domain": "hack.com"},
        headers=headers_b,
    )
    assert response.status_code == 400


# =========================================================
# Obtener assets
# =========================================================

def test_get_asset(client: TestClient) -> None:
    """Miembro puede ver su asset."""
    data = _register_with_org(client, "get@test.com", "get-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    create_response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": "get-test.com"},
        headers=headers,
    )
    asset_id = create_response.json()["id"]

    response = client.get(f"/api/v1/assets/{asset_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == asset_id


def test_get_asset_not_member(client: TestClient) -> None:
    """Usuario sin acceso → 404."""
    # Usuario A con asset
    data_a = _register_with_org(client, "a-get@test.com", "a-get-org")
    headers_a = _auth(data_a["access_token"])
    org_a_id = data_a["organization"]["id"]

    create_response = client.post(
        f"/api/v1/assets/organizations/{org_a_id}/assets",
        json={"domain": "private.com"},
        headers=headers_a,
    )
    asset_id = create_response.json()["id"]

    # Usuario B
    data_b = _register_with_org(client, "b-get@test.com", "b-get-org")
    headers_b = _auth(data_b["access_token"])

    response = client.get(f"/api/v1/assets/{asset_id}", headers=headers_b)
    assert response.status_code == 404


# =========================================================
# Actualizar assets
# =========================================================

def test_update_asset(client: TestClient) -> None:
    """Miembro puede actualizar su asset."""
    data = _register_with_org(client, "upd@test.com", "upd-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    create_response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": "update-test.com", "display_name": "Original"},
        headers=headers,
    )
    asset_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/assets/{asset_id}",
        json={"display_name": "Actualizado"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Actualizado"


# =========================================================
# Eliminar assets
# =========================================================

def test_delete_asset(client: TestClient) -> None:
    """Miembro puede eliminar su asset."""
    data = _register_with_org(client, "del@test.com", "del-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    create_response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": "delete-test.com"},
        headers=headers,
    )
    asset_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/assets/{asset_id}", headers=headers)
    assert response.status_code == 204

    # Ya no aparece
    list_response = client.get(
        f"/api/v1/assets/organizations/{org_id}/assets",
        headers=headers,
    )
    assert list_response.json() == []


# =========================================================
# Verificar assets
# =========================================================

def test_verify_asset(client: TestClient) -> None:
    """Miembro puede verificar su asset (simulado)."""
    data = _register_with_org(client, "verify@test.com", "verify-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    create_response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": "verify-test.com"},
        headers=headers,
    )
    asset_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/assets/{asset_id}/verify",
        headers=headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["verified"] is True
    assert result["record_type"] == "TXT"
    assert "_secureaudit.verify-test.com" == result["record_name"]

    # Verificar que el status cambió a active
    get_response = client.get(f"/api/v1/assets/{asset_id}", headers=headers)
    assert get_response.json()["status"] == "active"
    assert get_response.json()["verified_at"] is not None
