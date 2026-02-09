# Runbook migrations PostgreSQL (`app_qe`)

Ce runbook décrit comment :
1. ajouter temporairement les grants à `app_qe`,
2. lancer les migrations Alembic,
3. retirer les grants de `app_qe`.

## Pré-requis

- Base: `carthographie`
- Rôle applicatif: `app_qe`
- Service Docker: `quiz-engine`
- Exécuter les commandes SQL avec un compte admin PostgreSQL (`postgres` ou équivalent).

## 1) Ajouter les grants pour `app_qe`

```sql
-- Connexion à la base cible (exemple)
-- \c carthographie

GRANT CONNECT ON DATABASE carthographie TO app_qe;

-- Schéma dédié recommandé pour quiz-engine
CREATE SCHEMA IF NOT EXISTS qe AUTHORIZATION app_qe;
GRANT USAGE, CREATE ON SCHEMA qe TO app_qe;

-- Important: public doit être utilisable aussi (Alebmic/version table selon config)
GRANT USAGE, CREATE ON SCHEMA public TO app_qe;

-- Search path pour les CREATE pendant migration
ALTER ROLE app_qe IN DATABASE carthographie SET search_path = qe, public;
```

### Vérification rapide (optionnel)

```sql
SELECT
  current_user,
  current_setting('search_path', true) AS search_path;
```

## 2) Lancer les migrations

Depuis le repo:

```bash
docker compose -f docker-compose.yml exec quiz-engine /bin/sh -lc '
DATABASE_URL="${DB_SCHEME}://${DB_USER}:$(cat /run/secrets/qe_password.txt)@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
uv run alembic upgrade head
'
```

Vérifier la révision courante:

```bash
docker compose -f docker-compose.yml exec quiz-engine /bin/sh -lc '
DATABASE_URL="${DB_SCHEME}://${DB_USER}:$(cat /run/secrets/qe_password.txt)@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
uv run alembic current
'
```

## 3) Supprimer les grants de `app_qe`

Quand les migrations sont terminées, retirer les droits élargis:

```sql
-- Retrait des droits de création
REVOKE CREATE ON SCHEMA public FROM app_qe;
REVOKE CREATE ON SCHEMA qe FROM app_qe;

-- Optionnel: retirer USAGE si l'app ne doit plus lire ces schémas
-- REVOKE USAGE ON SCHEMA public FROM app_qe;
-- REVOKE USAGE ON SCHEMA qe FROM app_qe;

-- Remettre un search_path plus strict (ou défaut)
ALTER ROLE app_qe IN DATABASE carthographie SET search_path = qe;
```

### Nettoyage plus strict (optionnel)

Si `app_qe` ne doit plus se connecter du tout:

```sql
REVOKE CONNECT ON DATABASE carthographie FROM app_qe;
```

## Notes

- Ne pas faire `DROP SCHEMA qe` si des tables `qe_*` sont utilisées par l'application.
- Si des objets ont été créés avec un autre owner, ajuster l'ownership avant de révoquer.
