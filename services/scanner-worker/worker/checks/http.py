"""Checks de seguridad HTTP."""

import httpx

from worker.config import settings


def check_http(domain: str, timeout: int = 10) -> list[dict]:
    """Ejecuta checks HTTP sobre un dominio. Retorna lista de findings."""
    findings = []
    url = f"https://{domain}"

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            max_redirects=settings.HTTP_MAX_REDIRECTS,
            headers={"User-Agent": settings.HTTP_USER_AGENT},
        ) as client:
            response = client.get(url)
    except httpx.TimeoutException:
        findings.append({
            "category": "http", "check_name": "http_connection",
            "status": "fail", "severity": "high",
            "title": "Timeout en conexión HTTP",
            "description": f"No se pudo conectar a {url} en {timeout}s.",
            "evidence": {"url": url, "timeout": timeout},
            "recommendation": "Verificar que el servicio HTTP responda correctamente.",
        })
        return findings
    except httpx.RequestError as exc:
        findings.append({
            "category": "http", "check_name": "http_connection",
            "status": "fail", "severity": "high",
            "title": "Error de conexión HTTP",
            "description": str(exc),
            "evidence": {"url": url, "error": str(exc)},
            "recommendation": "Verificar que el servicio HTTP esté activo.",
        })
        return findings

    headers = {k.lower(): v for k, v in response.headers.items()}

    # Check 1: HSTS
    if "strict-transport-security" not in headers:
        findings.append({
            "category": "http", "check_name": "hsts",
            "status": "fail", "severity": "medium",
            "title": "Falta header HSTS",
            "description": "No se encontró Strict-Transport-Security.",
            "evidence": {"header": "Strict-Transport-Security"},
            "recommendation": "Añadir HSTS con max-age >= 31536000.",
        })
    else:
        findings.append({
            "category": "http", "check_name": "hsts",
            "status": "pass", "severity": "info",
            "title": "HSTS presente",
            "description": None,
            "evidence": {"value": headers["strict-transport-security"]},
            "recommendation": None,
        })

    # Check 2: X-Frame-Options / CSP frame-ancestors
    has_frame_protection = (
        "x-frame-options" in headers
        or "frame-ancestors" in headers.get("content-security-policy", "")
    )
    if not has_frame_protection:
        findings.append({
            "category": "http", "check_name": "clickjacking_protection",
            "status": "fail", "severity": "medium",
            "title": "Falta protección contra clickjacking",
            "description": "No se encontró X-Frame-Options ni CSP frame-ancestors.",
            "evidence": {},
            "recommendation": "Añadir X-Frame-Options: DENY o CSP frame-ancestors 'none'.",
        })
    else:
        findings.append({
            "category": "http", "check_name": "clickjacking_protection",
            "status": "pass", "severity": "info",
            "title": "Protección contra clickjacking presente",
            "description": None,
            "evidence": {},
            "recommendation": None,
        })

    # Check 3: Content-Security-Policy
    if "content-security-policy" not in headers:
        findings.append({
            "category": "http", "check_name": "csp",
            "status": "warn", "severity": "low",
            "title": "Falta Content-Security-Policy",
            "description": "No se encontró el header CSP.",
            "evidence": {},
            "recommendation": "Configurar CSP para reducir XSS.",
        })
    else:
        findings.append({
            "category": "http", "check_name": "csp",
            "status": "pass", "severity": "info",
            "title": "CSP presente",
            "description": None,
            "evidence": {"value": headers["content-security-policy"][:200]},
            "recommendation": None,
        })

    # Check 4: X-Content-Type-Options
    if headers.get("x-content-type-options", "").lower() != "nosniff":
        findings.append({
            "category": "http", "check_name": "x_content_type_options",
            "status": "fail", "severity": "low",
            "title": "Falta X-Content-Type-Options: nosniff",
            "description": "El header no está o no tiene el valor correcto.",
            "evidence": {"value": headers.get("x-content-type-options")},
            "recommendation": "Añadir X-Content-Type-Options: nosniff.",
        })
    else:
        findings.append({
            "category": "http", "check_name": "x_content_type_options",
            "status": "pass", "severity": "info",
            "title": "X-Content-Type-Options presente",
            "description": None,
            "evidence": {"value": "nosniff"},
            "recommendation": None,
        })

    # Check 5: Server header (info leak)
    if "server" in headers:
        findings.append({
            "category": "http", "check_name": "server_header_leak",
            "status": "warn", "severity": "low",
            "title": "Header Server expone información",
            "description": f"Server: {headers['server']}",
            "evidence": {"server": headers["server"]},
            "recommendation": "Ocultar o minimizar el header Server.",
        })

    return findings
