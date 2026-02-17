> Snapshot note: this export reflects a fresh rebuild on 2026-02-17 from migrations `0001` to `0007`.
> Source DB: `carthographie` (PostgreSQL 18.1 (Debian 18.1-1.pgdg13+2)), queried as user `app_qe`.

| id | version | description | applied_at | applied_by |
|---|---|---|---|---|
| 1 | 0001_create_qe_core_tables | Create initial qe_* tables and enum types | 2026-02-10 07:52:21.924900+00:00 | carthographie |
| 2 | 0002_seed_service_settings | Seed default service settings | 2026-02-10 07:52:38.419906+00:00 | carthographie |
| 3 | 0003_replace_answer_result_with_stage_event_outcome | Replace qe_answer/qe_question_result with qe_stage_event/qe_stage_outcome | 2026-02-10 07:52:51.929156+00:00 | carthographie |
| 4 | 0004_normalize_slide_markdown_payloads | Normalize SLIDE plugin specs with content.body and content.body_format | 2026-02-14 13:41:02.960819+00:00 | carthographie |
| 5 | 0005_rename_session_state_ended_to_finished | Rename qe_session_state enum value ENDED to FINISHED for contract alignment | 2026-02-17 10:26:25.469346+00:00 | carthographie |
| 6 | 0006_add_runtime_session_stage_and_score_entry | Add session started_at/current_stage_index and explicit qe_stage/qe_score_entry persistence | 2026-02-17 10:26:33.239234+00:00 | carthographie |
| 7 | 0007_enforce_stage_outcome_immutability | Enforce qe_stage_outcome immutability with unique business keys and mutation-blocking triggers | 2026-02-17 13:20:26.312763+00:00 | carthographie |
