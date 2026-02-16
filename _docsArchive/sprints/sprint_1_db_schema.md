# Sprint 1 — DB schema (qe_* only)

## Règle d’isolation (base partagée)
- Quiz-engine ne crée/modifie/supprime QUE des tables `qe_*`.
- Interdiction totale de FK vers des tables non `qe_*` (dont `auth_user`).
- Aucune hypothèse sur la présence/structure des tables communes.

## Revue des tables (sans champs)

### Identité & rôles (service-level)
- `qe_user`
  - Référence d’un utilisateur connecté (identity fournie par le hub via subject OIDC).
- `qe_user_role`
  - Rôles quiz-engine : `admin`, `moderator` (cumulables).

### Consentements & audit
- `qe_consent`
  - Stocke l’état des consentements par scope (`pseudo`, `history`, `email`), avec version, dates, expiration/revalidation.
- `qe_consent_audit` (optionnel mais recommandé)
  - Journal append-only des changements de consentement (preuve, debug, traçabilité).

### Configuration service
- `qe_service_setting`
  - Paramètres globaux (service open/closed, consent review months, rétention, etc.).

### Quiz & sessions
- `qe_quiz`
  - Stockage du quiz JSON opaque + version de `schema_version`.
- `qe_session`
  - Une partie (référence quiz + host + état lifecycle).
- `qe_player`
  - Un participant à une session (guest ou connecté).
- `qe_stage_event`
  - Réponses brutes (opaque).
- `qe_stage_outcome`
  - Résultats agrégés par question (opaque, plugin-owned).

### Historique & email
- Pas de tables dédiées en Sprint 1.
- Les besoins `history`/`email` sont cadrés côté consentements, mais la
  persistance dédiée est reportée à un sprint ultérieur.

## Règles de consentements (service-level)
Scopes :
- `pseudo` : obligatoire, sinon pas de service
- `history` : optionnel, retrait => suppression différée des données d’historique
- `email` : optionnel, requis pour emails “résultats/liens”

Expiration/revalidation :
- Consentements des utilisateurs connectés sont revalidés tous les X mois (config admin).
- Consentement expiré => fonctionnalités suspendues, mais aucune suppression de données.
- Suppression uniquement si retrait explicite (history=false) + purge différée.

Guests :
- Un guest doit consentir `pseudo` à chaque session (scope session).
- Pseudo guest suffixé `-qe` pour éviter collisions d’affichage avec users connectés.

Emails de modération :
- Les modérateurs peuvent envoyer des emails de type `moderation_notice` même si `email=false`.
- Cette exception doit être explicitement mentionnée dans les règles du service (transparence).
- Les emails “résultats/liens” restent strictement soumis à `email=true`.

## Index / contraintes (niveau intention)
- Unicité : `qe_session.session_code`
- Index : `qe_player.session_id`, `qe_answer.session_id`, `qe_question_result.session_id`
- Index : `qe_user.subject` (unique)
- Aucun index/contrainte ne doit cibler des tables externes.
