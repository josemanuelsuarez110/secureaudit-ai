"""Tests de checks TLS."""

import ssl
from unittest.mock import patch

import pytest

from worker.checks.tls import check_tls


def _make_cert(days_left: int = 90) -> dict:
    """Genera un certificado mock con N días de validez."""
    from datetime import datetime, timedelta, timezone

    expiry = datetime.now(timezone.utc) + timedelta(days=days_left)
    return {
        "notAfter": expiry.strftime("%b %d %H:%M:%S %Y GMT"),
    }


def test_tls_valid_certificate() -> None:
    """Certificado válido con TLS 1.3 y cipher fuerte → pass."""
    mock_data = {
        "cert": _make_cert(90),
        "cipher": ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256),
        "version": "TLSv1.3",
    }
    with patch("worker.checks.tls._fetch_certificate", return_value=mock_data):
        findings = check_tls("example.com")

    assert len(findings) == 3
    names = {f["check_name"]: f for f in findings}
    assert names["tls_version"]["status"] == "pass"
    assert names["cipher_suite"]["status"] == "pass"
    assert names["certificate_expiry"]["status"] == "pass"


def test_tls_old_version() -> None:
    """TLS 1.1 → fail (high)."""
    mock_data = {
        "cert": _make_cert(90),
        "cipher": ("TLS_AES_256_GCM_SHA384", "TLSv1.1", 256),
        "version": "TLSv1.1",
    }
    with patch("worker.checks.tls._fetch_certificate", return_value=mock_data):
        findings = check_tls("example.com")

    version_finding = next(f for f in findings if f["check_name"] == "tls_version")
    assert version_finding["status"] == "fail"
    assert version_finding["severity"] == "high"


def test_tls_expired_certificate() -> None:
    """Certificado expirado → fail (critical)."""
    mock_data = {
        "cert": _make_cert(-5),
        "cipher": ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256),
        "version": "TLSv1.3",
    }
    with patch("worker.checks.tls._fetch_certificate", return_value=mock_data):
        findings = check_tls("example.com")

    expiry = next(f for f in findings if f["check_name"] == "certificate_expiry")
    assert expiry["status"] == "fail"
    assert expiry["severity"] == "critical"


def test_tls_certificate_expiring_soon() -> None:
    """Certificado expira en 15 días → warn (medium)."""
    mock_data = {
        "cert": _make_cert(15),
        "cipher": ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256),
        "version": "TLSv1.3",
    }
    with patch("worker.checks.tls._fetch_certificate", return_value=mock_data):
        findings = check_tls("example.com")

    expiry = next(f for f in findings if f["check_name"] == "certificate_expiry")
    assert expiry["status"] == "warn"
    assert expiry["severity"] == "medium"


def test_tls_weak_cipher() -> None:
    """Cipher RC4 → fail (high)."""
    mock_data = {
        "cert": _make_cert(90),
        "cipher": ("RC4-SHA", "TLSv1.2", 128),
        "version": "TLSv1.2",
    }
    with patch("worker.checks.tls._fetch_certificate", return_value=mock_data):
        findings = check_tls("example.com")

    cipher = next(f for f in findings if f["check_name"] == "cipher_suite")
    assert cipher["status"] == "fail"
    assert cipher["severity"] == "high"


def test_tls_connection_error() -> None:
    """Error de conexión → fail (high) con 1 solo finding."""
    with patch(
        "worker.checks.tls._fetch_certificate",
        side_effect=ConnectionRefusedError("connection refused"),
    ):
        findings = check_tls("example.com")

    assert len(findings) == 1
    assert findings[0]["check_name"] == "tls_connection"
    assert findings[0]["status"] == "fail"


def test_tls_invalid_certificate() -> None:
    """Certificado inválido → fail (critical)."""
    with patch(
        "worker.checks.tls._fetch_certificate",
        side_effect=ssl.SSLCertVerificationError("invalid cert"),
    ):
        findings = check_tls("example.com")

    assert len(findings) == 1
    assert findings[0]["check_name"] == "tls_certificate_valid"
    assert findings[0]["severity"] == "critical"
