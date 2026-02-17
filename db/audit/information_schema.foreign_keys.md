| constraint_schema | table_name | source_column | constraint_name | target_schema | target_table | target_column | update_rule | delete_rule |
|---|---|---|---|---|---|---|---|---|
| qe | qe_consent | user_id | qe_consent_user_id_fkey | qe | qe_user | id | NO ACTION | CASCADE |
| qe | qe_consent_audit | user_id | qe_consent_audit_user_id_fkey | qe | qe_user | id | NO ACTION | CASCADE |
| qe | qe_player | session_id | qe_player_session_id_fkey | qe | qe_session | id | NO ACTION | CASCADE |
| qe | qe_player | user_id | qe_player_user_id_fkey | qe | qe_user | id | NO ACTION | NO ACTION |
| qe | qe_quiz | created_by_user_id | qe_quiz_created_by_user_id_fkey | qe | qe_user | id | NO ACTION | NO ACTION |
| qe | qe_score_entry | session_id | qe_score_entry_session_id_fkey | qe | qe_session | id | NO ACTION | CASCADE |
| qe | qe_score_entry | session_id | qe_score_entry_stage_triplet_fkey | qe | qe_stage | session_id | NO ACTION | NO ACTION |
| qe | qe_score_entry | stage_id | qe_score_entry_stage_triplet_fkey | qe | qe_stage | stage_id | NO ACTION | NO ACTION |
| qe | qe_score_entry | stage_index | qe_score_entry_stage_triplet_fkey | qe | qe_stage | stage_index | NO ACTION | NO ACTION |
| qe | qe_session | host_user_id | qe_session_host_user_id_fkey | qe | qe_user | id | NO ACTION | NO ACTION |
| qe | qe_session | quiz_id | qe_session_quiz_id_fkey | qe | qe_quiz | id | NO ACTION | NO ACTION |
| qe | qe_stage | session_id | qe_stage_session_id_fkey | qe | qe_session | id | NO ACTION | CASCADE |
| qe | qe_stage_event | session_id | qe_stage_event_session_id_fkey | qe | qe_session | id | NO ACTION | CASCADE |
| qe | qe_stage_outcome | session_id | qe_stage_outcome_session_id_fkey | qe | qe_session | id | NO ACTION | CASCADE |
| qe | qe_user_role | user_id | qe_user_role_user_id_fkey | qe | qe_user | id | NO ACTION | CASCADE |
