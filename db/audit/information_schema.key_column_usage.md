| table_schema | table_name | constraint_name | column_name | ordinal_position | position_in_unique_constraint |
|---|---|---|---|---|---|
| qe | qe_consent | qe_consent_pkey | id | 1 | |
| qe | qe_consent | qe_consent_user_id_fkey | user_id | 1 | 1 |
| qe | qe_consent | uq_qe_consent_user_id | user_id | 1 | |
| qe | qe_consent | uq_qe_consent_user_id | scope | 2 | |
| qe | qe_consent_audit | qe_consent_audit_pkey | id | 1 | |
| qe | qe_consent_audit | qe_consent_audit_user_id_fkey | user_id | 1 | 1 |
| qe | qe_player | qe_player_pkey | id | 1 | |
| qe | qe_player | qe_player_player_code_key | player_code | 1 | |
| qe | qe_player | qe_player_session_id_fkey | session_id | 1 | 1 |
| qe | qe_player | qe_player_user_id_fkey | user_id | 1 | 1 |
| qe | qe_quiz | qe_quiz_created_by_user_id_fkey | created_by_user_id | 1 | 1 |
| qe | qe_quiz | qe_quiz_pkey | id | 1 | |
| qe | qe_schema_migration | qe_schema_migration_pkey | id | 1 | |
| qe | qe_schema_migration | qe_schema_migration_version_key | version | 1 | |
| qe | qe_service_setting | qe_service_setting_pkey | key | 1 | |
| qe | qe_session | qe_session_host_user_id_fkey | host_user_id | 1 | 1 |
| qe | qe_session | qe_session_pkey | id | 1 | |
| qe | qe_session | qe_session_quiz_id_fkey | quiz_id | 1 | 1 |
| qe | qe_session | qe_session_session_code_key | session_code | 1 | |
| qe | qe_stage_event | qe_stage_event_pkey | id | 1 | |
| qe | qe_stage_event | qe_stage_event_session_id_fkey | session_id | 1 | 1 |
| qe | qe_stage_outcome | qe_stage_outcome_pkey | id | 1 | |
| qe | qe_stage_outcome | qe_stage_outcome_session_id_fkey | session_id | 1 | 1 |
| qe | qe_user | qe_user_pkey | id | 1 | |
| qe | qe_user | qe_user_subject_key | subject | 1 | |
| qe | qe_user_role | qe_user_role_pkey | id | 1 | |
| qe | qe_user_role | qe_user_role_user_id_fkey | user_id | 1 | 1 |
| qe | qe_user_role | uq_qe_user_role_user_id | user_id | 1 | |
| qe | qe_user_role | uq_qe_user_role_user_id | role | 2 | |