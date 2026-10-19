"""Checks de seguridad DNS (SPF, DMARC, CAA)."""

import dns.resolver
import dns.exception


def _resolve_txt(domain: str, timeout: float = 5.0) -> list[str]:
    """Resuelve registros TXT de un dominio."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        answers = resolver.resolve(domain, "TXT")
        return [
            b"".join(rdata.strings).decode("utf-8", errors="ignore")
            for rdata in answers
        ]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
            dns.resolver.NoNameservers, dns.exception.Timeout):
        return []
    except Exception:
        return []


def _resolve_caa(domain: str, timeout: float = 5.0) -> list[str]:
    """Resuelve registros CAA de un dominio."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        answers = resolver.resolve(domain, "CAA")
        return [str(rdata) for rdata in answers]
    except Exception:
        return []


def check_dns(domain: str, timeout: float = 5.0) -> list[dict]:
    """Ejecuta checks DNS sobre un dominio. Retorna lista de findings."""
    findings = []

    # Check 1: SPF
    txt_records = _resolve_txt(domain, timeout)
    spf = [r for r in txt_records if r.lower().startswith("v=spf1")]

    if not spf:
        findings.append({
            "category": "dns", "check_name": "spf",
            "status": "fail", "severity": "medium",
            "title": "Falta registro SPF",
            "description": "No se encontró registro SPF (v=spf1).",
            "evidence": {},
            "recommendation": "Añadir registro TXT con SPF para prevenir spoofing de email.",
        })
    elif len(spf) > 1:
        findings.append({
            "category": "dns", "check_name": "spf",
            "status": "fail", "severity": "high",
            "title": "Múltiples registros SPF",
            "description": f"Se encontraron {len(spf)} registros SPF. Solo debe haber 1.",
            "evidence": {"count": len(spf)},
            "recommendation": "Unificar todos los SPF en un solo registro.",
        })
    elif "+all" in spf[0].lower():
        findings.append({
            "category": "dns", "check_name": "spf",
            "status": "fail", "severity": "critical",
            "title": "SPF demasiado permisivo (+all)",
            "description": "El registro SPF permite cualquier servidor enviar email.",
            "evidence": {"spf": spf[0]},
            "recommendation": "Cambiar +all por ~all o -all.",
        })
    else:
        findings.append({
            "category": "dns", "check_name": "spf",
            "status": "pass", "severity": "info",
            "title": "SPF configurado correctamente",
            "description": None,
            "evidence": {"spf": spf[0][:200]},
            "recommendation": None,
        })

    # Check 2: DMARC
    dmarc_records = _resolve_txt(f"_dmarc.{domain}", timeout)
    dmarc = [r for r in dmarc_records if r.lower().startswith("v=dmarc1")]

    if not dmarc:
        findings.append({
            "category": "dns", "check_name": "dmarc",
            "status": "fail", "severity": "medium",
            "title": "Falta registro DMARC",
            "description": "No se encontró registro DMARC en _dmarc.",
            "evidence": {},
            "recommendation": "Añadir TXT _dmarc con política p=quarantine o p=reject.",
        })
    elif "p=none" in dmarc[0].lower():
        findings.append({
            "category": "dns", "check_name": "dmarc",
            "status": "warn", "severity": "low",
            "title": "DMARC en modo monitor (p=none)",
            "description": "DMARC no bloquea emails sospechosos.",
            "evidence": {"dmarc": dmarc[0][:200]},
            "recommendation": "Cambiar a p=quarantine o p=reject.",
        })
    else:
        findings.append({
            "category": "dns", "check_name": "dmarc",
            "status": "pass", "severity": "info",
            "title": "DMARC configurado",
            "description": None,
            "evidence": {"dmarc": dmarc[0][:200]},
            "recommendation": None,
        })

    # Check 3: CAA
    caa_records = _resolve_caa(domain, timeout)
    if not caa_records:
        findings.append({
            "category": "dns", "check_name": "caa",
            "status": "warn", "severity": "low",
            "title": "Falta registro CAA",
            "description": "No se encontró registro CAA.",
            "evidence": {},
            "recommendation": "Añadir CAA para restringir qué CAs pueden emitir certificados.",
        })
    else:
        findings.append({
            "category": "dns", "check_name": "caa",
            "status": "pass", "severity": "info",
            "title": "CAA configurado",
            "description": None,
            "evidence": {"records": caa_records},
            "recommendation": None,
        })

    return findings
