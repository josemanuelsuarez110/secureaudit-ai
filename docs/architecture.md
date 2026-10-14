# Arquitectura — SecureAudit AI

## Componentes

1. Frontend (Next.js) — UI para clientes
2. API (FastAPI) — Lógica de negocio, autenticación, RLS
3. Scanner Worker — Motor de auditoría en background
4. PostgreSQL — Base de datos con RLS
5. Cola persistente — Implementada con PostgreSQL

## Diagrama

Cliente → Vercel (Next.js) → FastAPI → PostgreSQL (RLS)
                                    ↓
                              Scanner Worker
                              (TLS, HTTP, DNS)

## Decisiones técnicas

- PostgreSQL con RLS: aislamiento multi-tenant a nivel DB
- Cola en PostgreSQL: evita Redis/Celery en el MVP
- NO Kubernetes: complejidad innecesaria para el MVP

## Modelo de datos

- organizations, memberships, assets, asset_verifications
- scan_jobs, scan_results, findings, reports
- audit_events, subscriptions

## Flujo de auditoría

1. Cliente registra activo (dominio)
2. Sistema genera token DNS TXT
3. Cliente añade TXT a su DNS
4. Sistema verifica
5. Cliente autoriza
6. API encola scan_job
7. Worker procesa (TLS, HTTP, DNS)
8. Guarda resultados
9. Clasifica findings
10. Cliente descarga informe PDF
