# Runbook migrations SQL PostgreSQL (`app_qe`)

Ce runbook décrit comment :
1. ajouter temporairement les grants à `app_qe`,
2. lancer les migrations SQL manuelles,
3. supprimer les grants de `app_qe`.

## Pré-requis

- Base: `carthographie`
- Rôle applicatif: `app_qe`
- Scripts SQL: `db/migrations/sql/*.sql`
- Les scripts sont exécutés par l'admin (ou via `SET ROLE app_qe`).

## 1) Ajouter les grants pour `app_qe`

Exécuter en admin PostgreSQL :

```sql
GRANT CONNECT ON DATABASE carthographie TO app_qe;

CREATE SCHEMA IF NOT EXISTS qe AUTHORIZATION app_qe;
GRANT USAGE, CREATE ON SCHEMA qe TO app_qe;
GRANT USAGE, CREATE ON SCHEMA public TO app_qe;

ALTER ROLE app_qe IN DATABASE carthographie SET search_path = qe, public;
```

## 2) Lancer les migrations SQL (manuelles)

Option simple (admin dans `psql`) :

```sql
\c carthographie
SET ROLE app_qe;
\set ON_ERROR_STOP on
\i db/migrations/sql/0001_create_qe_core_tables.sql
\i db/migrations/sql/0002_seed_service_settings.sql
\i db/migrations/sql/0003_replace_answer_result_with_stage_event_outcome.sql
RESET ROLE;
```

Option shell (admin) :

```bash
psql -v ON_ERROR_STOP=1 -d carthographie -f db/migrations/sql/0001_create_qe_core_tables.sql
psql -v ON_ERROR_STOP=1 -d carthographie -f db/migrations/sql/0002_seed_service_settings.sql
psql -v ON_ERROR_STOP=1 -d carthographie -f db/migrations/sql/0003_replace_answer_result_with_stage_event_outcome.sql
```

### Vérifier quelles migrations ont été appliquées

```sql
SET search_path TO qe, public;
SELECT version, applied_at, applied_by
FROM qe_schema_migration
ORDER BY applied_at, id;
```

## 3) Supprimer les grants de `app_qe`

Quand les migrations sont terminées :

```sql
REVOKE CREATE ON SCHEMA public FROM app_qe;
REVOKE CREATE ON SCHEMA qe FROM app_qe;

ALTER ROLE app_qe IN DATABASE carthographie SET search_path = qe;
```

Optionnel (si tu veux bloquer toute connexion ensuite) :

```sql
REVOKE CONNECT ON DATABASE carthographie FROM app_qe;
```

## Notes

- Les scripts SQL sont idempotents autant que possible (`IF EXISTS`, `IF NOT EXISTS`, `ON CONFLICT DO NOTHING`).
- En cas d'état partiel ancien, nettoyer les objets `qe_*` et les types `qe_*` avant de relancer `0001`.
