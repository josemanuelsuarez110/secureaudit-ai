# SecureAudit AI

SaaS B2B de auditoría continua de seguridad para pymes, agencias digitales y consultoras de TI.

## Visión

Permitir que cualquier empresa conozca sus configuraciones de seguridad expuestas y supervise su corrección, sin necesidad de un equipo de seguridad dedicado.

## MVP (v1.0)

| Módulo | Función |
|--------|---------|
| 1. Empresas y usuarios | Registro, organizaciones, roles, multi-tenant |
| 2. Activos autorizados | Registro de dominios, verificación DNS TXT |
| 3. Auditoría técnica | Análisis TLS, certificados, cabeceras HTTP, DNS |
| 4. Riesgos y remediación | Findings clasificados por severidad |
| 5. Informes | PDF con resumen ejecutivo y detalle técnico |

## Stack

- Frontend: Next.js + TypeScript + Tailwind
- Backend: FastAPI + Python
- Base de datos: PostgreSQL 16 con RLS
- Motor de auditoría: Python, HTTPX, SSL, DNS
- Informes: ReportLab
- CI/CD: GitHub Actions
- Deploy: Vercel + servicio Python con worker

## Principios de seguridad

1. Nunca confiar en tenant_id desde el cliente
2. RLS en todas las consultas multiempresa
3. Autorización verificable (DNS TXT) antes de auditar
4. Sin explotación, fuerza bruta ni escaneo agresivo
5. Informes y evidencias en almacenamiento privado

## Roadmap

| Semana | Foco |
|--------|------|
| 1 | Estructura base + documentación + CI |
| 2 | Autenticación + RLS |
| 3-4 | Motor de auditoría (TLS/HTTP/DNS) |
| 5 | Dashboard + informes PDF |
| 6 | Seguridad + deploy staging |
| 7-8 | Pilotos con clientes reales |

## Modelo de negocio

| Plan | Precio | Activos | Auditorías/mes |
|------|--------|---------|----------------|
| Starter | $29/mes | 3 | 4 |
| Professional | $79/mes | 15 | 30 |
| Business | $149/mes | 50 | 100 |

## Licencia

Propietario. Todos los derechos reservados.
