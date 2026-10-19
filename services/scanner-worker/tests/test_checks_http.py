"""Tests de checks HTTP."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from worker.checks.http import check_http


def _mock_response(headers: dict, status_code: int = 200) -> MagicMock:
    """Crea un mock de httpx.Response."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = httpx.Headers(headers)
    return response


def _find(findings: list[dict], check_name: str) -> dict:
    return next(f for f in findings if f["check_name"] == check_name)


def test_http_all_headers_present() -> None:
    """Todos los headers de seguridad presentes → pass."""
    headers = {
        "strict-transport-security": "max-age=31536000",
        "x-frame-options": "DENY",
        "content-security-policy": "default-src 'self'",
        "x-content-type-options": "nosniff",
    }
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(headers)
        findings = check_http("example.com")

    assert _find(findings, "hsts")["status"] == "pass"
    assert _find(findings, "clickjacking_protection")["status"] == "pass"
    assert _find(findings, "csp")["status"] == "pass"
    assert _find(findings, "x_content_type_options")["status"] == "pass"


def test_http_missing_hsts() -> None:
    """Falta HSTS → fail (medium)."""
    headers = {}
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(headers)
        findings = check_http("example.com")

    hsts = _find(findings, "hsts")
    assert hsts["status"] == "fail"
    assert hsts["severity"] == "medium"


def test_http_missing_clickjacking_protection() -> None:
    """Falta X-Frame-Options y CSP frame-ancestors → fail (medium)."""
    headers = {"strict-transport-security": "max-age=31536000"}
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(headers)
        findings = check_http("example.com")

    click = _find(findings, "clickjacking_protection")
    assert click["status"] == "fail"
    assert click["severity"] == "medium"


def test_http_missing_csp() -> None:
    """Falta CSP → warn (low)."""
    headers = {"strict-transport-security": "max-age=31536000"}
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(headers)
        findings = check_http("example.com")

    csp = _find(findings, "csp")
    assert csp["status"] == "warn"
    assert csp["severity"] == "low"


def test_http_missing_x_content_type() -> None:
    """Falta X-Content-Type-Options: nosniff → fail (low)."""
    headers = {"strict-transport-security": "max-age=31536000"}
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(headers)
        findings = check_http("example.com")

    xcto = _find(findings, "x_content_type_options")
    assert xcto["status"] == "fail"
    assert xcto["severity"] == "low"


def test_http_server_header_leak() -> None:
    """Header Server presente → warn (low)."""
    headers = {
        "strict-transport-security": "max-age=31536000",
        "x-frame-options": "DENY",
        "content-security-policy": "default-src 'self'",
        "x-content-type-options": "nosniff",
        "server": "nginx/1.18.0",
    }
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(headers)
        findings = check_http("example.com")

    server = _find(findings, "server_header_leak")
    assert server["status"] == "warn"
    assert server["severity"] == "low"


def test_http_timeout() -> None:
    """Timeout → fail (high) con 1 solo finding."""
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("timeout")
        findings = check_http("example.com")

    assert len(findings) == 1
    assert findings[0]["check_name"] == "http_connection"
    assert findings[0]["severity"] == "high"


def test_http_connection_error() -> None:
    """Error de conexión → fail (high) con 1 solo finding."""
    with patch("worker.checks.http.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("connection refused")
        findings = check_http("example.com")

    assert len(findings) == 1
    assert findings[0]["check_name"] == "http_connection"
    assert findings[0]["severity"] == "high"
