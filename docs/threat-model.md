# Threat Model — SecureAudit AI

## Activos

1. Datos de clientes
2. Credenciales (JWT, API keys)
3. Resultados de auditoría
4. Informes PDF
5. Infraestructura

## Amenazas

### T1: Fuga multi-tenant
- Vector: SQL sin filtro por organization_id
- Mitigación: RLS + contexto por transacción

### T2: SSRF desde worker
- Vector: dominio malicioso apuntando a IPs internas
- Mitigación: bloquear rangos privados, redirecciones, límites

### T3: Auditoría no autorizada
- Vector: auditar dominios sin control
- Mitigación: DNS TXT + autorización expresa

### T4: Inyección SQL
- Mitigación: ORM + parámetros + validación

### T5: Robo de JWT
- Mitigación: HTTPS + HttpOnly + CSP

### T6: DoS al worker
- Mitigación: límite de jobs + cola + prioridades

### T7: Enumeración de usuarios
- Mitigación: respuestas genéricas

### T8: Escalada de privilegios
- Mitigación: verificación de roles en cada endpoint

### T9: Fuga en logs
- Mitigación: logs estructurados + filtrado

### T10: Dependencias vulnerables
- Mitigación: Dependabot + auditorías

## Modelo de confianza

- Nunca confiar en: tenant_id del cliente, roles declarados
- Siempre verificar: JWT + pertenencia + rol
