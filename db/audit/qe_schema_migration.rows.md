> Snapshot note: this export reflects a fresh rebuild on 2026-02-17 from migrations `0001` to `0007`.
> Source DB: `qe_audit_refresh` (PostgreSQL 16), applied by user `postgres`.

| id | version | description | applied_at | applied_by |
|---|---|---|---|---|
| 1 | 0001_create_qe_core_tables | Create initial qe_* tables and enum types | 2026-02-17 10:24:14.636814+00 | postgres |
| 2 | 0002_seed_service_settings | Seed default service settings | 2026-02-17 10:24:14.754858+00 | postgres |
| 3 | 0003_replace_answer_result_with_stage_event_outcome | Replace qe_answer/qe_question_result with qe_stage_event/qe_stage_outcome | 2026-02-17 10:24:14.821618+00 | postgres |
| 4 | 0004_normalize_slide_markdown_payloads | Normalize SLIDE plugin specs with content.body and content.body_format | 2026-02-17 10:24:14.902996+00 | postgres |
| 5 | 0005_rename_session_state_ended_to_finished | Rename qe_session_state enum value ENDED to FINISHED for contract alignment | 2026-02-17 10:24:14.970038+00 | postgres |
| 6 | 0006_add_runtime_session_stage_and_score_entry | Add session started_at/current_stage_index and explicit qe_stage/qe_score_entry persistence | 2026-02-17 10:24:15.035646+00 | postgres |
| 7 | 0007_enforce_stage_outcome_immutability | Enforce qe_stage_outcome immutability with unique business keys and mutation-blocking triggers | 2026-02-17 10:24:15.116316+00 | postgres |
