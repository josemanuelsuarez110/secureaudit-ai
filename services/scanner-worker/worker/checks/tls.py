"""Checks de seguridad TLS."""

import socket
import ssl
from datetime import datetime, timezone


def _fetch_certificate(domain: str, timeout: int = 10) -> dict:
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    with socket.create_connection((domain, 443), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            return {
                "cert": ssock.getpeercert(),
                "cipher": ssock.cipher(),
                "version": ssock.version(),
            }


def check_tls(domain: str, timeout: int = 10) -> list[dict]:
    findings = []

    try:
        data = _fetch_certificate(domain, timeout)
    except ssl.SSLCertVerificationError as exc:
        findings.append({
            "category": "tls", "check_name": "tls_certificate_valid",
            "status": "fail", "severity": "critical",
            "title": "Certificado TLS inválido",
            "description": f"No se pudo validar: {exc}",
            "evidence": {"error": str(exc)},
            "recommendation": "Renovar o configurar correctamente el certificado.",
        })
        return findings
    except (socket.timeout, socket.gaierror, ConnectionRefusedError) as exc:
        findings.append({
            "category": "tls", "check_name": "tls_connection",
            "status": "fail", "severity": "high",
            "title": "No se pudo conectar por HTTPS",
            "description": f"Error de conexión: {exc}",
            "evidence": {"error": str(exc)},
            "recommendation": "Verificar que HTTPS esté activo.",
        })
        return findings
    except Exception as exc:
        findings.append({
            "category": "tls", "check_name": "tls_unknown",
            "status": "error", "severity": "info",
            "title": "Error desconocido en TLS",
            "description": str(exc),
            "evidence": {"error": str(exc)},
            "recommendation": None,
        })
        return findings

    cert, cipher, version = data["cert"], data["cipher"], data["version"]

    # Versión TLS
    if version and version.startswith("TLSv1") and version < "TLSv1.2":
        findings.append({
            "category": "tls", "check_name": "tls_version",
            "status": "fail", "severity": "high",
            "title": f"Versión TLS obsoleta: {version}",
            "description": "TLS 1.0/1.1 son inseguros.",
            "evidence": {"version": version},
            "recommendation": "Configurar TLS 1.2 o superior.",
        })
    else:
        findings.append({
            "category": "tls", "check_name": "tls_version",
            "status": "pass", "severity": "info",
            "title": f"Versión TLS: {version}",
            "description": None, "evidence": {"version": version},
            "recommendation": None,
        })

    # Expiración
    not_after = cert.get("notAfter")
    if not_after:
        try:
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            days_left = (expiry - datetime.now(timezone.utc)).days
            if days_left < 0:
                findings.append({
                    "category": "tls", "check_name": "certificate_expiry",
                    "status": "fail", "severity": "critical",
                    "title": "Certificado TLS expirado",
                    "description": f"Expiró hace {-days_left} días.",
                    "evidence": {"expires_at": not_after, "days_left": days_left},
                    "recommendation": "Renovar certificado inmediatamente.",
                })
            elif days_left < 30:
                findings.append({
                    "category": "tls", "check_name": "certificate_expiry",
                    "status": "warn", "severity": "medium",
                    "title": f"Certificado expira en {days_left} días",
                    "description": "Expira pronto.",
                    "evidence": {"expires_at": not_after, "days_left": days_left},
                    "recommendation": "Renovar antes de la expiración.",
                })
            else:
                findings.append({
                    "category": "tls", "check_name": "certificate_expiry",
                    "status": "pass", "severity": "info",
                    "title": f"Certificado válido ({days_left} días)",
                    "description": None,
                    "evidence": {"expires_at": not_after, "days_left": days_left},
                    "recommendation": None,
                })
        except Exception:
            pass

    # Cipher suite
    if cipher:
        cipher_name = cipher[0]
        weak = ["RC4", "DES", "3DES", "MD5", "NULL", "EXPORT"]
        if any(w in cipher_name.upper() for w in weak):
            findings.append({
                "category": "tls", "check_name": "cipher_suite",
                "status": "fail", "severity": "high",
                "title": f"Cipher suite débil: {cipher_name}",
                "description": "Cipher suite inseguro.",
                "evidence": {"cipher": cipher_name},
                "recommendation": "Deshabilitar cipher suites débiles.",
            })
        else:
            findings.append({
                "category": "tls", "check_name": "cipher_suite",
                "status": "pass", "severity": "info",
                "title": f"Cipher suite: {cipher_name}",
                "description": None, "evidence": {"cipher": cipher_name},
                "recommendation": None,
            })

    return findings
