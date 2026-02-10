| table_schema | table_name | constraint_name | constraint_type |
|---|---|---|---|
| qe | qe_consent | qe_consent_granted_at_not_null | CHECK |
| qe | qe_consent | qe_consent_id_not_null | CHECK |
| qe | qe_consent | qe_consent_policy_version_not_null | CHECK |
| qe | qe_consent | qe_consent_scope_not_null | CHECK |
| qe | qe_consent | qe_consent_status_not_null | CHECK |
| qe | qe_consent | qe_consent_updated_at_not_null | CHECK |
| qe | qe_consent | qe_consent_user_id_not_null | CHECK |
| qe | qe_consent | qe_consent_user_id_fkey | FOREIGN KEY |
| qe | qe_consent | qe_consent_pkey | PRIMARY KEY |
| qe | qe_consent | uq_qe_consent_user_id | UNIQUE |
| qe | qe_consent_audit | qe_consent_audit_action_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_created_at_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_id_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_policy_version_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_scope_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_user_id_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_user_id_fkey | FOREIGN KEY |
| qe | qe_consent_audit | qe_consent_audit_pkey | PRIMARY KEY |
| qe | qe_player | qe_player_id_not_null | CHECK |
| qe | qe_player | qe_player_is_guest_not_null | CHECK |
| qe | qe_player | qe_player_joined_at_not_null | CHECK |
| qe | qe_player | qe_player_nickname_not_null | CHECK |
| qe | qe_player | qe_player_player_code_not_null | CHECK |
| qe | qe_player | qe_player_session_id_not_null | CHECK |
| qe | qe_player | qe_player_session_id_fkey | FOREIGN KEY |
| qe | qe_player | qe_player_user_id_fkey | FOREIGN KEY |
| qe | qe_player | qe_player_pkey | PRIMARY KEY |
| qe | qe_player | qe_player_player_code_key | UNIQUE |
| qe | qe_quiz | qe_quiz_created_at_not_null | CHECK |
| qe | qe_quiz | qe_quiz_id_not_null | CHECK |
| qe | qe_quiz | qe_quiz_payload_not_null | CHECK |
| qe | qe_quiz | qe_quiz_schema_version_not_null | CHECK |
| qe | qe_quiz | qe_quiz_updated_at_not_null | CHECK |
| qe | qe_quiz | qe_quiz_created_by_user_id_fkey | FOREIGN KEY |
| qe | qe_quiz | qe_quiz_pkey | PRIMARY KEY |
| qe | qe_schema_migration | qe_schema_migration_applied_at_not_null | CHECK |
| qe | qe_schema_migration | qe_schema_migration_applied_by_not_null | CHECK |
| qe | qe_schema_migration | qe_schema_migration_description_not_null | CHECK |
| qe | qe_schema_migration | qe_schema_migration_id_not_null | CHECK |
| qe | qe_schema_migration | qe_schema_migration_version_not_null | CHECK |
| qe | qe_schema_migration | qe_schema_migration_pkey | PRIMARY KEY |
| qe | qe_schema_migration | qe_schema_migration_version_key | UNIQUE |
| qe | qe_service_setting | qe_service_setting_key_not_null | CHECK |
| qe | qe_service_setting | qe_service_setting_updated_at_not_null | CHECK |
| qe | qe_service_setting | qe_service_setting_value_not_null | CHECK |
| qe | qe_service_setting | qe_service_setting_pkey | PRIMARY KEY |
| qe | qe_session | qe_session_created_at_not_null | CHECK |
| qe | qe_session | qe_session_id_not_null | CHECK |
| qe | qe_session | qe_session_session_code_not_null | CHECK |
| qe | qe_session | qe_session_state_not_null | CHECK |
| qe | qe_session | qe_session_updated_at_not_null | CHECK |
| qe | qe_session | qe_session_host_user_id_fkey | FOREIGN KEY |
| qe | qe_session | qe_session_quiz_id_fkey | FOREIGN KEY |
| qe | qe_session | qe_session_pkey | PRIMARY KEY |
| qe | qe_session | qe_session_session_code_key | UNIQUE |
| qe | qe_stage_event | qe_stage_event_created_at_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_id_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_payload_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_session_id_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_stage_id_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_stage_index_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_session_id_fkey | FOREIGN KEY |
| qe | qe_stage_event | qe_stage_event_pkey | PRIMARY KEY |
| qe | qe_stage_outcome | qe_stage_outcome_created_at_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_id_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_payload_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_session_id_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_stage_id_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_stage_index_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_session_id_fkey | FOREIGN KEY |
| qe | qe_stage_outcome | qe_stage_outcome_pkey | PRIMARY KEY |
| qe | qe_user | qe_user_created_at_not_null | CHECK |
| qe | qe_user | qe_user_id_not_null | CHECK |
| qe | qe_user | qe_user_subject_not_null | CHECK |
| qe | qe_user | qe_user_updated_at_not_null | CHECK |
| qe | qe_user | qe_user_pkey | PRIMARY KEY |
| qe | qe_user | qe_user_subject_key | UNIQUE |
| qe | qe_user_role | qe_user_role_created_at_not_null | CHECK |
| qe | qe_user_role | qe_user_role_id_not_null | CHECK |
| qe | qe_user_role | qe_user_role_role_not_null | CHECK |
| qe | qe_user_role | qe_user_role_user_id_not_null | CHECK |
| qe | qe_user_role | qe_user_role_user_id_fkey | FOREIGN KEY |
| qe | qe_user_role | qe_user_role_pkey | PRIMARY KEY |
| qe | qe_user_role | uq_qe_user_role_user_id | UNIQUE |