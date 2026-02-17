| table_schema | table_name | constraint_name | constraint_type |
|---|---|---|---|
| qe | qe_consent | 16389_16514_1_not_null | CHECK |
| qe | qe_consent | 16389_16514_2_not_null | CHECK |
| qe | qe_consent | 16389_16514_3_not_null | CHECK |
| qe | qe_consent | 16389_16514_4_not_null | CHECK |
| qe | qe_consent | 16389_16514_5_not_null | CHECK |
| qe | qe_consent | 16389_16514_6_not_null | CHECK |
| qe | qe_consent | 16389_16514_9_not_null | CHECK |
| qe | qe_consent | qe_consent_user_id_fkey | FOREIGN KEY |
| qe | qe_consent | qe_consent_pkey | PRIMARY KEY |
| qe | qe_consent | uq_qe_consent_user_id | UNIQUE |
| qe | qe_consent_audit | 16389_16530_1_not_null | CHECK |
| qe | qe_consent_audit | 16389_16530_2_not_null | CHECK |
| qe | qe_consent_audit | 16389_16530_3_not_null | CHECK |
| qe | qe_consent_audit | 16389_16530_4_not_null | CHECK |
| qe | qe_consent_audit | 16389_16530_5_not_null | CHECK |
| qe | qe_consent_audit | 16389_16530_6_not_null | CHECK |
| qe | qe_consent_audit | qe_consent_audit_user_id_fkey | FOREIGN KEY |
| qe | qe_consent_audit | qe_consent_audit_pkey | PRIMARY KEY |
| qe | qe_player | 16389_16543_1_not_null | CHECK |
| qe | qe_player | 16389_16543_2_not_null | CHECK |
| qe | qe_player | 16389_16543_4_not_null | CHECK |
| qe | qe_player | 16389_16543_5_not_null | CHECK |
| qe | qe_player | 16389_16543_6_not_null | CHECK |
| qe | qe_player | 16389_16543_7_not_null | CHECK |
| qe | qe_player | qe_player_session_id_fkey | FOREIGN KEY |
| qe | qe_player | qe_player_user_id_fkey | FOREIGN KEY |
| qe | qe_player | qe_player_pkey | PRIMARY KEY |
| qe | qe_player | qe_player_player_code_key | UNIQUE |
| qe | qe_quiz | 16389_16461_1_not_null | CHECK |
| qe | qe_quiz | 16389_16461_2_not_null | CHECK |
| qe | qe_quiz | 16389_16461_3_not_null | CHECK |
| qe | qe_quiz | 16389_16461_5_not_null | CHECK |
| qe | qe_quiz | 16389_16461_6_not_null | CHECK |
| qe | qe_quiz | qe_quiz_created_by_user_id_fkey | FOREIGN KEY |
| qe | qe_quiz | qe_quiz_pkey | PRIMARY KEY |
| qe | qe_schema_migration | 16389_16391_1_not_null | CHECK |
| qe | qe_schema_migration | 16389_16391_2_not_null | CHECK |
| qe | qe_schema_migration | 16389_16391_3_not_null | CHECK |
| qe | qe_schema_migration | 16389_16391_4_not_null | CHECK |
| qe | qe_schema_migration | 16389_16391_5_not_null | CHECK |
| qe | qe_schema_migration | qe_schema_migration_pkey | PRIMARY KEY |
| qe | qe_schema_migration | qe_schema_migration_version_key | UNIQUE |
| qe | qe_score_entry | 16389_16657_11_not_null | CHECK |
| qe | qe_score_entry | 16389_16657_1_not_null | CHECK |
| qe | qe_score_entry | 16389_16657_2_not_null | CHECK |
| qe | qe_score_entry | 16389_16657_3_not_null | CHECK |
| qe | qe_score_entry | 16389_16657_4_not_null | CHECK |
| qe | qe_score_entry | 16389_16657_5_not_null | CHECK |
| qe | qe_score_entry | 16389_16657_6_not_null | CHECK |
| qe | qe_score_entry | ck_qe_score_entry_grade_bounds | CHECK |
| qe | qe_score_entry | ck_qe_score_entry_grade_pair | CHECK |
| qe | qe_score_entry | ck_qe_score_entry_presence | CHECK |
| qe | qe_score_entry | ck_qe_score_entry_schema_version | CHECK |
| qe | qe_score_entry | qe_score_entry_session_id_fkey | FOREIGN KEY |
| qe | qe_score_entry | qe_score_entry_pkey | PRIMARY KEY |
| qe | qe_service_setting | 16389_16452_1_not_null | CHECK |
| qe | qe_service_setting | 16389_16452_2_not_null | CHECK |
| qe | qe_service_setting | 16389_16452_3_not_null | CHECK |
| qe | qe_service_setting | qe_service_setting_pkey | PRIMARY KEY |
| qe | qe_session | 16389_16477_1_not_null | CHECK |
| qe | qe_session | 16389_16477_2_not_null | CHECK |
| qe | qe_session | 16389_16477_5_not_null | CHECK |
| qe | qe_session | 16389_16477_6_not_null | CHECK |
| qe | qe_session | 16389_16477_7_not_null | CHECK |
| qe | qe_session | qe_session_host_user_id_fkey | FOREIGN KEY |
| qe | qe_session | qe_session_quiz_id_fkey | FOREIGN KEY |
| qe | qe_session | qe_session_pkey | PRIMARY KEY |
| qe | qe_session | qe_session_session_code_key | UNIQUE |
| qe | qe_stage | 16389_16634_1_not_null | CHECK |
| qe | qe_stage | 16389_16634_2_not_null | CHECK |
| qe | qe_stage | 16389_16634_3_not_null | CHECK |
| qe | qe_stage | 16389_16634_4_not_null | CHECK |
| qe | qe_stage | 16389_16634_5_not_null | CHECK |
| qe | qe_stage | 16389_16634_6_not_null | CHECK |
| qe | qe_stage | 16389_16634_7_not_null | CHECK |
| qe | qe_stage | 16389_16634_8_not_null | CHECK |
| qe | qe_stage | 16389_16634_9_not_null | CHECK |
| qe | qe_stage | ck_qe_stage_status | CHECK |
| qe | qe_stage | qe_stage_session_id_fkey | FOREIGN KEY |
| qe | qe_stage | qe_stage_pkey | PRIMARY KEY |
| qe | qe_stage | uq_qe_stage_session_stage_id | UNIQUE |
| qe | qe_stage | uq_qe_stage_session_stage_index | UNIQUE |
| qe | qe_stage_event | 16389_16602_1_not_null | CHECK |
| qe | qe_stage_event | 16389_16602_2_not_null | CHECK |
| qe | qe_stage_event | 16389_16602_3_not_null | CHECK |
| qe | qe_stage_event | 16389_16602_4_not_null | CHECK |
| qe | qe_stage_event | 16389_16602_5_not_null | CHECK |
| qe | qe_stage_event | 16389_16602_6_not_null | CHECK |
| qe | qe_stage_event | qe_stage_event_session_id_fkey | FOREIGN KEY |
| qe | qe_stage_event | qe_stage_event_pkey | PRIMARY KEY |
| qe | qe_stage_outcome | 16389_16618_1_not_null | CHECK |
| qe | qe_stage_outcome | 16389_16618_2_not_null | CHECK |
| qe | qe_stage_outcome | 16389_16618_3_not_null | CHECK |
| qe | qe_stage_outcome | 16389_16618_4_not_null | CHECK |
| qe | qe_stage_outcome | 16389_16618_5_not_null | CHECK |
| qe | qe_stage_outcome | 16389_16618_6_not_null | CHECK |
| qe | qe_stage_outcome | qe_stage_outcome_session_id_fkey | FOREIGN KEY |
| qe | qe_stage_outcome | qe_stage_outcome_pkey | PRIMARY KEY |
| qe | qe_stage_outcome | uq_qe_stage_outcome_session_stage_id | UNIQUE |
| qe | qe_stage_outcome | uq_qe_stage_outcome_session_stage_index | UNIQUE |
| qe | qe_user | 16389_16442_1_not_null | CHECK |
| qe | qe_user | 16389_16442_2_not_null | CHECK |
| qe | qe_user | 16389_16442_3_not_null | CHECK |
| qe | qe_user | 16389_16442_4_not_null | CHECK |
| qe | qe_user | qe_user_pkey | PRIMARY KEY |
| qe | qe_user | qe_user_subject_key | UNIQUE |
| qe | qe_user_role | 16389_16499_1_not_null | CHECK |
| qe | qe_user_role | 16389_16499_2_not_null | CHECK |
| qe | qe_user_role | 16389_16499_3_not_null | CHECK |
| qe | qe_user_role | 16389_16499_4_not_null | CHECK |
| qe | qe_user_role | qe_user_role_user_id_fkey | FOREIGN KEY |
| qe | qe_user_role | qe_user_role_pkey | PRIMARY KEY |
| qe | qe_user_role | uq_qe_user_role_user_id | UNIQUE |
