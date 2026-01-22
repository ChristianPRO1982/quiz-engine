# Sprint 1 — Configuration (DB, auth hub, consentements, i18n)

## DB
### Variables
- `DATABASE_URL` (obligatoire)
  - ex : `mysql+mysqldb://user:pass@host:3306/shared_db`
- `DB_ECHO` (optionnel)
- `ENV` (optionnel)

### Règles
- La DB peut être partagée ou dédiée : aucune hypothèse dans le code.
- Le service doit rester portable (autre VPS) via configuration uniquement.

## Auth (hub / Option A)
Quiz-engine ne crée pas de comptes. Il consomme une identité (token) fournie par le hub.

Variables typiques (à ajuster selon ton provider OIDC/OAuth) :
- `AUTH_ISSUER_URL`
- `AUTH_CLIENT_ID`
- `AUTH_CLIENT_SECRET` (si applicable)
- `AUTH_REDIRECT_URL`
- `AUTH_JWKS_URL` (si validation JWT via JWKS)
- `AUTH_AUDIENCE` (si utilisé)

## Consentements (service-level)
- `CONSENT_REVIEW_MONTHS` (obligatoire, admin-configurable via DB)
  - nombre de mois avant revalidation des consentements des users connectés
- `HISTORY_PURGE_HOUR` (optionnel)
  - heure de purge quotidienne (ex: 05:00)
- `HISTORY_PURGE_GRACE_HOURS` (optionnel)
  - délai avant purge (ex: 24h)

## I18n (gettext)
Objectif : aucun texte “façade” hardcodé, EN/FR minimum.

### Stratégie
- gettext via fichiers `.po` (sources) et `.mo` (compilés)
- les templates Jinja2 utilisent `_()` pour traduire
- les textes de consentement sont référencés par clé versionnée :
  - `consent.pseudo.v1.body`, `consent.history.v1.body`, `consent.email.v1.body`
- quiz-engine stocke le `policy_version` accepté, pas le texte.

### Règles de dev
- Toute nouvelle phrase visible utilisateur doit passer par gettext
- Toute modification de wording de consentement => bump de version (`v2`) + relecture PJ
