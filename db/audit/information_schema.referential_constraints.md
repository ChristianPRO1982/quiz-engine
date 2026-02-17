| constraint_schema | table_name | constraint_name | unique_constraint_schema | unique_constraint_name | match_option | update_rule | delete_rule |
|---|---|---|---|---|---|---|---|
| qe | qe_consent | qe_consent_user_id_fkey | qe | qe_user_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_consent_audit | qe_consent_audit_user_id_fkey | qe | qe_user_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_player | qe_player_session_id_fkey | qe | qe_session_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_player | qe_player_user_id_fkey | qe | qe_user_pkey | NONE | NO ACTION | NO ACTION |
| qe | qe_quiz | qe_quiz_created_by_user_id_fkey | qe | qe_user_pkey | NONE | NO ACTION | NO ACTION |
| qe | qe_score_entry | qe_score_entry_session_id_fkey | qe | qe_session_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_session | qe_session_host_user_id_fkey | qe | qe_user_pkey | NONE | NO ACTION | NO ACTION |
| qe | qe_session | qe_session_quiz_id_fkey | qe | qe_quiz_pkey | NONE | NO ACTION | NO ACTION |
| qe | qe_stage | qe_stage_session_id_fkey | qe | qe_session_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_stage_event | qe_stage_event_session_id_fkey | qe | qe_session_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_stage_outcome | qe_stage_outcome_session_id_fkey | qe | qe_session_pkey | NONE | NO ACTION | CASCADE |
| qe | qe_user_role | qe_user_role_user_id_fkey | qe | qe_user_pkey | NONE | NO ACTION | CASCADE |
