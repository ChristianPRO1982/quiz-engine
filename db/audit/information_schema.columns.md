| table_schema | table_name | ordinal_position | column_name | data_type | is_nullable | column_default |
|--------|-------|---------|--------|------|----------|---------|
| qe | qe_consent | 1 | id | integer | NO | nextval('qe_consent_id_seq'::regclass) |
| qe | qe_consent | 2 | user_id | integer | NO | [NULL] |
| qe | qe_consent | 3 | scope | USER-DEFINED | NO | [NULL] |
| qe | qe_consent | 4 | status | USER-DEFINED | NO | [NULL] |
| qe | qe_consent | 5 | policy_version | character varying | NO | [NULL] |
| qe | qe_consent | 6 | granted_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_consent | 7 | revoked_at | timestamp with time zone | YES | [NULL] |
| qe | qe_consent | 8 | expires_at | timestamp with time zone | YES | [NULL] |
| qe | qe_consent | 9 | updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_consent_audit | 1 | id | integer | NO | nextval('qe_consent_audit_id_seq'::regclass) |
| qe | qe_consent_audit | 2 | user_id | integer | NO | [NULL] |
| qe | qe_consent_audit | 3 | scope | USER-DEFINED | NO | [NULL] |
| qe | qe_consent_audit | 4 | action | USER-DEFINED | NO | [NULL] |
| qe | qe_consent_audit | 5 | policy_version | character varying | NO | [NULL] |
| qe | qe_consent_audit | 6 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_player | 1 | id | integer | NO | nextval('qe_player_id_seq'::regclass) |
| qe | qe_player | 2 | session_id | integer | NO | [NULL] |
| qe | qe_player | 3 | user_id | integer | YES | [NULL] |
| qe | qe_player | 4 | player_code | character varying | NO | [NULL] |
| qe | qe_player | 5 | nickname | character varying | NO | [NULL] |
| qe | qe_player | 6 | is_guest | boolean | NO | true |
| qe | qe_player | 7 | joined_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_player | 8 | left_at | timestamp with time zone | YES | [NULL] |
| qe | qe_quiz | 1 | id | integer | NO | nextval('qe_quiz_id_seq'::regclass) |
| qe | qe_quiz | 2 | schema_version | character varying | NO | [NULL] |
| qe | qe_quiz | 3 | payload | json | NO | [NULL] |
| qe | qe_quiz | 4 | created_by_user_id | integer | YES | [NULL] |
| qe | qe_quiz | 5 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_quiz | 6 | updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_schema_migration | 1 | id | bigint | NO | nextval('qe_schema_migration_id_seq'::regclass) |
| qe | qe_schema_migration | 2 | version | character varying | NO | [NULL] |
| qe | qe_schema_migration | 3 | description | text | NO | [NULL] |
| qe | qe_schema_migration | 4 | applied_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_schema_migration | 5 | applied_by | text | NO | CURRENT_USER |
| qe | qe_service_setting | 1 | key | character varying | NO | [NULL] |
| qe | qe_service_setting | 2 | value | text | NO | [NULL] |
| qe | qe_service_setting | 3 | updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_session | 1 | id | integer | NO | nextval('qe_session_id_seq'::regclass) |
| qe | qe_session | 2 | session_code | character varying | NO | [NULL] |
| qe | qe_session | 3 | quiz_id | integer | YES | [NULL] |
| qe | qe_session | 4 | host_user_id | integer | YES | [NULL] |
| qe | qe_session | 5 | state | USER-DEFINED | NO | 'LOBBY'::qe_session_state |
| qe | qe_session | 6 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_session | 7 | updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_session | 8 | ended_at | timestamp with time zone | YES | [NULL] |
| qe | qe_stage_event | 1 | id | integer | NO | nextval('qe_stage_event_id_seq'::regclass) |
| qe | qe_stage_event | 2 | session_id | integer | NO | [NULL] |
| qe | qe_stage_event | 3 | stage_id | character varying | NO | [NULL] |
| qe | qe_stage_event | 4 | stage_index | integer | NO | [NULL] |
| qe | qe_stage_event | 5 | payload | json | NO | [NULL] |
| qe | qe_stage_event | 6 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_stage_outcome | 1 | id | integer | NO | nextval('qe_stage_outcome_id_seq'::regclass) |
| qe | qe_stage_outcome | 2 | session_id | integer | NO | [NULL] |
| qe | qe_stage_outcome | 3 | stage_id | character varying | NO | [NULL] |
| qe | qe_stage_outcome | 4 | stage_index | integer | NO | [NULL] |
| qe | qe_stage_outcome | 5 | payload | json | NO | [NULL] |
| qe | qe_stage_outcome | 6 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_user | 1 | id | integer | NO | nextval('qe_user_id_seq'::regclass) |
| qe | qe_user | 2 | subject | character varying | NO | [NULL] |
| qe | qe_user | 3 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_user | 4 | updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| qe | qe_user_role | 1 | id | integer | NO | nextval('qe_user_role_id_seq'::regclass) |
| qe | qe_user_role | 2 | user_id | integer | NO | [NULL] |
| qe | qe_user_role | 3 | role | USER-DEFINED | NO | [NULL] |
| qe | qe_user_role | 4 | created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |