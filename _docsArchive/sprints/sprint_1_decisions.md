# Sprint 1 — ADR light (décisions)

## ADR-001 — Préfixe `qe_` obligatoire
Toutes les tables du service quiz-engine sont préfixées `qe_`.
Motif : DB partagée, suppression/maintenance sûres, zéro collision.

## ADR-002 — Alembic autorisé mais filtré (qe-only)
Alembic/autogenerate est utilisé, mais ne gère QUE les tables `qe_*`.
Motif : garder confort dev + éviter toute action sur tables communes.

## ADR-003 — Auth déléguée au hub ; consentements portés par quiz-engine
Le hub fournit l’identité (subject/token). Quiz-engine stocke et impose ses consentements.
Motif : chaque service a ses règles et finalités ; pas de consentement global imposé par le hub.

## ADR-004 — Consentements séparés et versionnés
Scopes :
- `pseudo` obligatoire (sinon pas de service)
- `history` optionnel (retrait => purge différée)
- `email` optionnel (résultats/liens)
Motif : clarté UX, conformité, contrôle fin.

## ADR-005 — Expiration ≠ suppression
Si un consentement expire : fonctionnalités suspendues jusqu’à revalidation, mais aucune suppression de données.
Suppression uniquement lors d’un retrait explicite (history=false) + purge différée.
Motif : éviter la perte surprise + garder un comportement prévisible.

## ADR-006 — Modération email (exception cadrée)
Un modérateur/admin peut envoyer des emails de type `moderation_notice` même si `email=false`.
Les emails “résultats/liens” restent soumis à `email=true`.
Motif : sécurité/ordre du service, transparence dans les règles.

## ADR-007 — i18n via gettext ; wording non hardcodé
Tous les textes “façade” sont traduits via gettext (.po/.mo).
Les textes de consentement sont adressés via des clés versionnées.
Motif : relecture, traduction, audit, zéro hardcode.
