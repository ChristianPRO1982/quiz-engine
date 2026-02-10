# Sprint 1 — SQL migrations manuelles (qe_* only)

## Objectif
Utiliser des migrations SQL manuelles pour gérer uniquement le schéma `qe_*`,
sans jamais toucher les tables communes (Django auth + autres services).

## Règle de filtrage (obligatoire)
Les scripts SQL du service doivent :
- créer/modifier/supprimer uniquement des objets `qe_*`
- ignorer tout le reste (tables communes et autres services)
- historiser l'application dans `qe_schema_migration`

Conséquence attendue :
- aucun script SQL de migration ne doit référencer des tables hors `qe_*`.

## Conventions de migrations
- Une migration = un changement logique cohérent
- Message clair : `create qe_session and qe_player tables`
- Pas de migration “fourre-tout”
- Revue obligatoire avant merge (diff lisible)

## Workflow standard
Créer une migration :
```bash
# Créer un nouveau script SQL dans db/migrations/sql/
# ex: 0004_add_qe_xxx.sql
```

Appliquer :

```bash
psql -v ON_ERROR_STOP=1 -d carthographie -f db/migrations/sql/0001_create_qe_core_tables.sql
psql -v ON_ERROR_STOP=1 -d carthographie -f db/migrations/sql/0002_seed_service_settings.sql
psql -v ON_ERROR_STOP=1 -d carthographie -f db/migrations/sql/0003_replace_answer_result_with_stage_event_outcome.sql
```

Rollback :

```bash
# rollback manuel via script dédié (si prévu) ou restauration DB
```

### Garde-fous CI (requis)

CI doit échouer si une migration contient :

- création/modification/suppression de table sans préfixe `qe_`
- FK vers une table non `qe_*`
- mention explicite de tables communes (ex: `auth_user`)

Checklist CI recommandée :

- ☐ exécuter les scripts SQL sur DB vierge (ordre 0001 -> ... -> N)
- ☐ scan "qe-only" sur le contenu des scripts de migration
- ☐ vérifier `qe_schema_migration` après exécution

### Interdits

- Modifier une migration déjà appliquée (sauf stratégie explicitée de squash)
- Introduire une FK vers auth_user
- Utiliser les tables communes comme source de vérité (pas de coupling)
