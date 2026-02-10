| schemaname | tablename | indexname | indexdef |
|---|---|---|---|
| qe | qe_consent | qe_consent_pkey | CREATE UNIQUE INDEX qe_consent_pkey ON qe.qe_consent USING btree (id) |
| qe | qe_consent | uq_qe_consent_user_id | CREATE UNIQUE INDEX uq_qe_consent_user_id ON qe.qe_consent USING btree (user_id, scope) |
| qe | qe_consent_audit | qe_consent_audit_pkey | CREATE UNIQUE INDEX qe_consent_audit_pkey ON qe.qe_consent_audit USING btree (id) |
| qe | qe_player | ix_qe_player_session_id | CREATE INDEX ix_qe_player_session_id ON qe.qe_player USING btree (session_id) |
| qe | qe_player | qe_player_pkey | CREATE UNIQUE INDEX qe_player_pkey ON qe.qe_player USING btree (id) |
| qe | qe_player | qe_player_player_code_key | CREATE UNIQUE INDEX qe_player_player_code_key ON qe.qe_player USING btree (player_code) |
| qe | qe_quiz | qe_quiz_pkey | CREATE UNIQUE INDEX qe_quiz_pkey ON qe.qe_quiz USING btree (id) |
| qe | qe_schema_migration | qe_schema_migration_pkey | CREATE UNIQUE INDEX qe_schema_migration_pkey ON qe.qe_schema_migration USING btree (id) |
| qe | qe_schema_migration | qe_schema_migration_version_key | CREATE UNIQUE INDEX qe_schema_migration_version_key ON qe.qe_schema_migration USING btree (version) |
| qe | qe_service_setting | qe_service_setting_pkey | CREATE UNIQUE INDEX qe_service_setting_pkey ON qe.qe_service_setting USING btree (key) |
| qe | qe_session | qe_session_pkey | CREATE UNIQUE INDEX qe_session_pkey ON qe.qe_session USING btree (id) |
| qe | qe_session | qe_session_session_code_key | CREATE UNIQUE INDEX qe_session_session_code_key ON qe.qe_session USING btree (session_code) |
| qe | qe_stage_event | ix_qe_stage_event_session_id | CREATE INDEX ix_qe_stage_event_session_id ON qe.qe_stage_event USING btree (session_id) |
| qe | qe_stage_event | qe_stage_event_pkey | CREATE UNIQUE INDEX qe_stage_event_pkey ON qe.qe_stage_event USING btree (id) |
| qe | qe_stage_outcome | ix_qe_stage_outcome_session_id | CREATE INDEX ix_qe_stage_outcome_session_id ON qe.qe_stage_outcome USING btree (session_id) |
| qe | qe_stage_outcome | qe_stage_outcome_pkey | CREATE UNIQUE INDEX qe_stage_outcome_pkey ON qe.qe_stage_outcome USING btree (id) |
| qe | qe_user | qe_user_pkey | CREATE UNIQUE INDEX qe_user_pkey ON qe.qe_user USING btree (id) |
| qe | qe_user | qe_user_subject_key | CREATE UNIQUE INDEX qe_user_subject_key ON qe.qe_user USING btree (subject) |
| qe | qe_user_role | qe_user_role_pkey | CREATE UNIQUE INDEX qe_user_role_pkey ON qe.qe_user_role USING btree (id) |
| qe | qe_user_role | uq_qe_user_role_user_id | CREATE UNIQUE INDEX uq_qe_user_role_user_id ON qe.qe_user_role USING btree (user_id, role) |