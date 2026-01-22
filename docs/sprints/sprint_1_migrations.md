# Sprint 1 — Alembic migrations (qe_* only)

## Objectif
Utiliser Alembic + SQLAlchemy 2.0 pour gérer uniquement le schéma `qe_*`,
sans jamais toucher les tables communes (Django auth + autres services).

## Règle de filtrage (obligatoire)
Le mécanisme Alembic/autogenerate doit être configuré pour :
- inclure uniquement les tables dont le nom commence par `qe_`
- ignorer tout le reste (tables communes et autres services)

Conséquence attendue :
- `alembic revision --autogenerate` ne doit JAMAIS proposer de modifications hors `qe_*`.

## Conventions de migrations
- Une migration = un changement logique cohérent
- Message clair : `create qe_session and qe_player tables`
- Pas de migration “fourre-tout”
- Revue obligatoire avant merge (diff lisible)

## Workflow standard
Créer une migration :
```bash
uv run alembic revision --autogenerate -m "create qe_* core tables"
```

Appliquer :

```bash
uv run alembic upgrade head
```

Rollback :

```bash
uv run alembic downgrade -1
```

### Garde-fous CI (requis)

CI doit échouer si une migration contient :

- création/modification/suppression de table sans préfixe `qe_`
- FK vers une table non `qe_*`
- mention explicite de tables communes (ex: `auth_user`)

Checklist CI recommandée :

- ☐ alembic upgrade head sur DB vierge (ou db de test)
- ☐ alembic downgrade base
- ☐ alembic upgrade head à nouveau
- ☐ scan "qe-only" sur le contenu des scripts de migration

### Interdits

- Modifier une migration déjà appliquée (sauf stratégie explicitée de squash)
- Introduire une FK vers auth_user
- Utiliser les tables communes comme source de vérité (pas de coupling)