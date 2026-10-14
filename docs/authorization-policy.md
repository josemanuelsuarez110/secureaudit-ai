# Política de Autorización — SecureAudit AI

## Principios

1. Cero confianza en el cliente
2. Multi-tenant estricto (organization_id)
3. RLS obligatorio
4. Roles: admin, analyst, reader
5. Auditoría de acciones sensibles

## Roles

- admin: gestiona organización, usuarios, activos, facturación
- analyst: registra activos, ejecuta auditorías
- reader: solo lectura

## Contexto de organización

JWT incluye: user_id, organization_id, role
El servidor NO confía en organization_id del cliente
Lo resuelve desde memberships

## RLS

CREATE POLICY assets_isolation ON assets
  USING (organization_id = current_setting('app.current_organization')::uuid);

Aplicación establece: SET LOCAL app.current_organization = '<uuid>';

## Verificación de activos

1. Cliente registra dominio
2. Sistema genera token DNS TXT
3. Cliente añade TXT
4. Sistema verifica
5. Cliente autoriza
6. Solo entonces se audita

## Alcance

Permitido: TLS, HTTP, DNS, certificados
Prohibido: explotación, fuerza bruta, escaneo agresivo
