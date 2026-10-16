"""Tests de scans (auditorías)."""

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


def _create_verified_asset(
    client: TestClient,
    token: str,
    org_id: str,
    domain: str = "test.com",
    monkeypatch=None,
) -> str:
    """Helper: crea asset y lo verifica (con mock de DNS)."""
    # Crear asset
    response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": domain},
        headers=_auth(token),
    )
    assert response.status_code == 201
    asset_id = response.json()["id"]

    # Verificar con mock
    if monkeypatch:
        from app.services import asset as asset_module

        def mock_verify(*args, **kwargs):
            return True, "Verificación exitosa (mock)"

        monkeypatch.setattr(asset_module, "verify_txt_record", mock_verify)

    verify_response = client.post(
        f"/api/v1/assets/{asset_id}/verify",
        headers=_auth(token),
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["verified"] is True

    return asset_id


# =========================================================
# Listar scans
# =========================================================

def test_list_scans_empty(client: TestClient) -> None:
    """Usuario con org sin scans ve lista vacía."""
    data = _register_with_org(client, "empty@test.com", "empty-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    response = client.get(
        f"/api/v1/scans/organizations/{org_id}/scans",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_scans_requires_auth(client: TestClient) -> None:
    """Sin token → 401."""
    data = _register_with_org(client, "noauth@test.com", "noauth-org")
    org_id = data["organization"]["id"]

    response = client.get(f"/api/v1/scans/organizations/{org_id}/scans")
    assert response.status_code == 401


def test_list_scans_not_member(client: TestClient) -> None:
    """Usuario no miembro no puede listar → 403."""
    data_a = _register_with_org(client, "user-a@test.com", "user-a-org")
    org_a_id = data_a["organization"]["id"]

    data_b = _register_with_org(client, "user-b@test.com", "user-b-org")
    headers_b = _auth(data_b["access_token"])

    response = client.get(
        f"/api/v1/scans/organizations/{org_a_id}/scans",
        headers=headers_b,
    )
    assert response.status_code == 403


# =========================================================
# Crear scans
# =========================================================

def test_create_scan_job(client: TestClient, monkeypatch) -> None:
    """Miembro puede crear scan job para asset verificado."""
    data = _register_with_org(client, "create@test.com", "create-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data["access_token"], org_id, "create-test.com", monkeypatch
    )

    response = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json={"asset_id": asset_id, "scan_type": "full"},
        headers=headers,
    )
    assert response.status_code == 201
    job = response.json()
    assert job["asset_id"] == asset_id
    assert job["status"] == "pending"
    assert job["scan_type"] == "full"
    assert job["priority"] == 5


def test_create_scan_job_asset_not_verified(client: TestClient) -> None:
    """Asset sin verificar → 400."""
    data = _register_with_org(client, "noverif@test.com", "noverif-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    # Crear asset SIN verificar
    response = client.post(
        f"/api/v1/assets/organizations/{org_id}/assets",
        json={"domain": "noverif-test.com"},
        headers=headers,
    )
    asset_id = response.json()["id"]

    # Intentar crear scan
    response = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json={"asset_id": asset_id, "scan_type": "full"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "verificado" in response.json()["detail"].lower()


def test_create_scan_job_duplicate(client: TestClient, monkeypatch) -> None:
    """No se puede crear otro job si hay uno pendiente/en curso."""
    data = _register_with_org(client, "dup@test.com", "dup-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data["access_token"], org_id, "dup-test.com", monkeypatch
    )

    payload = {"asset_id": asset_id, "scan_type": "full"}

    # Primer job
    r1 = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json=payload,
        headers=headers,
    )
    assert r1.status_code == 201

    # Segundo job (debe fallar)
    r2 = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json=payload,
        headers=headers,
    )
    assert r2.status_code == 400
    assert "en curso" in r2.json()["detail"].lower()


def test_create_scan_job_invalid_scan_type(client: TestClient, monkeypatch) -> None:
    """scan_type inválido → 422."""
    data = _register_with_org(client, "invalid@test.com", "invalid-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data["access_token"], org_id, "invalid-test.com", monkeypatch
    )

    response = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json={"asset_id": asset_id, "scan_type": "INVALID"},
        headers=headers,
    )
    assert response.status_code == 422


# =========================================================
# Obtener scans
# =========================================================

def test_get_scan_job(client: TestClient, monkeypatch) -> None:
    """Miembro puede ver su scan job."""
    data = _register_with_org(client, "get@test.com", "get-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data["access_token"], org_id, "get-test.com", monkeypatch
    )

    create_response = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json={"asset_id": asset_id, "scan_type": "full"},
        headers=headers,
    )
    job_id = create_response.json()["id"]

    response = client.get(f"/api/v1/scans/{job_id}", headers=headers)
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == job_id
    assert job["results"] == []


def test_get_scan_job_not_member(client: TestClient, monkeypatch) -> None:
    """Usuario sin acceso → 404."""
    data_a = _register_with_org(client, "a-get@test.com", "a-get-org")
    headers_a = _auth(data_a["access_token"])
    org_a_id = data_a["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data_a["access_token"], org_a_id, "a-test.com", monkeypatch
    )

    create_response = client.post(
        f"/api/v1/scans/organizations/{org_a_id}/scans",
        json={"asset_id": asset_id, "scan_type": "full"},
        headers=headers_a,
    )
    job_id = create_response.json()["id"]

    # Usuario B
    data_b = _register_with_org(client, "b-get@test.com", "b-get-org")
    headers_b = _auth(data_b["access_token"])

    response = client.get(f"/api/v1/scans/{job_id}", headers=headers_b)
    assert response.status_code == 404


# =========================================================
# Cancelar scans
# =========================================================

def test_cancel_scan_job(client: TestClient, monkeypatch) -> None:
    """Miembro puede cancelar un job pendiente."""
    data = _register_with_org(client, "cancel@test.com", "cancel-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data["access_token"], org_id, "cancel-test.com", monkeypatch
    )

    create_response = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json={"asset_id": asset_id, "scan_type": "full"},
        headers=headers,
    )
    job_id = create_response.json()["id"]

    response = client.post(f"/api/v1/scans/{job_id}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


# =========================================================
# Resultados (aún vacíos)
# =========================================================

def test_get_scan_results_empty(client: TestClient, monkeypatch) -> None:
    """Job recién creado no tiene resultados."""
    data = _register_with_org(client, "res@test.com", "res-org")
    headers = _auth(data["access_token"])
    org_id = data["organization"]["id"]

    asset_id = _create_verified_asset(
        client, data["access_token"], org_id, "res-test.com", monkeypatch
    )

    create_response = client.post(
        f"/api/v1/scans/organizations/{org_id}/scans",
        json={"asset_id": asset_id, "scan_type": "full"},
        headers=headers,
    )
    job_id = create_response.json()["id"]

    response = client.get(f"/api/v1/scans/{job_id}/results", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
