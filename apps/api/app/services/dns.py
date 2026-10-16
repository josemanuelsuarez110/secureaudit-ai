"""Servicio de verificación DNS."""

import dns.resolver
import dns.exception


class DNSError(Exception):
    """Error de verificación DNS."""

    pass


def verify_txt_record(
    domain: str,
    expected_value: str,
    record_name: str | None = None,
    timeout: float = 5.0,
) -> tuple[bool, str]:
    """Verifica que un registro TXT exista con el valor esperado."""
    target = record_name or domain

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        answers = resolver.resolve(target, "TXT")
    except dns.resolver.NXDOMAIN:
        return False, f"El dominio {target} no existe"
    except dns.resolver.NoAnswer:
        return False, f"No se encontró registro TXT en {target}"
    except dns.resolver.NoNameservers:
        return False, f"Los nameservers de {target} no responden"
    except dns.exception.Timeout:
        return False, f"Timeout consultando DNS para {target}"
    except Exception as exc:
        return False, f"Error consultando DNS: {exc}"

    for rdata in answers:
        txt_value = b"".join(rdata.strings).decode("utf-8", errors="ignore")
        if expected_value in txt_value:
            return True, "Verificación exitosa"

    return False, "El registro TXT no contiene el valor esperado"
