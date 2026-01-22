# Sprint 1 — DB, migrations, conventions, consentements & i18n

## Objectif
Mettre en place la persistance MySQL pour quiz-engine en base partagée, avec :
- tables strictement préfixées `qe_`
- migrations Alembic sûres (autogenerate autorisé mais filtré)
- isolation totale vis-à-vis des tables communes / autres services
- cadre “consentements versionnés” (pseudo/history/email) + revalidation périodique
- i18n des textes “façade” via gettext (.po/.mo), sans hardcode

## Périmètre
### Inclus
- Conventions DB (noms, index, contraintes, rétention)
- Modèle de données `qe_*` (sans implémenter toute la logique applicative)
- Setup Alembic + workflow migrations
- Garde-fous CI sur migrations (qe-only)
- Modèle de consentements (états, expiration/revalidation, purge différée history)
- Stratégie i18n (gettext) + règles de versionnement des textes de consentement

### Exclus
- Implémentation complète UI “profil”
- Envoi d’emails (mécanique + providers)
- Features de modération (kick/ban) hors cadrage
- Plugins / scoring / interprétation des réponses (engine purity)

## Principes non négociables
- La DB est partagée : quiz-engine ne doit jamais toucher les tables hors `qe_*`.
- Aucune FK vers `auth_user` ou toute table commune.
- Le hub fournit l’identité, quiz-engine porte ses consentements spécifiques.
- Expiration de consentement ≠ suppression : la suppression n’arrive que lors d’un retrait explicite (history=false) + purge différée.

## Étapes (implémentation)
1) Définir le schéma `qe_*` minimal + index/contraintes
2) Définir les consentements (pseudo/history/email), leur cycle de vie et le modèle de stockage
3) Définir i18n : gettext + clés versionnées pour consentements
4) Initialiser Alembic avec filtre qe-only (autogenerate safe)
5) Ajouter garde-fous CI (migrations ne contenant que qe_)
6) Documenter le workflow dev (upgrade/downgrade, revue migrations, rollback)

## Definition of Done (DoD)
- [ ] Toutes les tables créées par le service commencent par `qe_`
- [ ] Autogenerate Alembic ne propose jamais de changements sur tables non `qe_*`
- [ ] CI échoue si une migration touche autre chose que `qe_*`
- [ ] Consentements : modèle + règles “expiration ≠ suppression” + purge différée history documentées
- [ ] i18n : aucun texte “façade” hardcodé ; stratégie gettext documentée
- [ ] Docs Sprint 1 validées (relecture PJ) et exploitables par Codex

## Risques & mitigations
- Risque : autogenerate “voit” toute la DB partagée
  - Mitigation : filtre Alembic qe-only + garde-fou CI
- Risque : confusion consentement “email” vs emails de modération
  - Mitigation : scopes distincts + catégorie “moderation_notice” documentée
- Risque : changements de wording sans traçabilité
  - Mitigation : consentements stockent (key + policy_version) ; textes via i18n versionné

## Références internes
- Règles Codex (formats / engine purity) : docs/CODEX_RULES.md
- Contrat projet (philosophie & limites) : docs/PROJECT_CONTRACT.md
