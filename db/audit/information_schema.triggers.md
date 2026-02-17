| trigger_schema | event_object_table | trigger_name | action_timing | event_manipulation | action_orientation | action_statement |
|---|---|---|---|---|---|---|
| qe | qe_score_entry | trg_qe_score_entry_no_delete | BEFORE | DELETE | ROW | EXECUTE FUNCTION qe.qe_forbid_score_entry_mutation() |
| qe | qe_score_entry | trg_qe_score_entry_no_truncate | BEFORE | TRUNCATE | STATEMENT | EXECUTE FUNCTION qe.qe_forbid_score_entry_mutation() |
| qe | qe_score_entry | trg_qe_score_entry_no_update | BEFORE | UPDATE | ROW | EXECUTE FUNCTION qe.qe_forbid_score_entry_mutation() |
| qe | qe_stage_outcome | trg_qe_stage_outcome_no_delete | BEFORE | DELETE | ROW | EXECUTE FUNCTION qe.qe_forbid_stage_outcome_mutation() |
| qe | qe_stage_outcome | trg_qe_stage_outcome_no_truncate | BEFORE | TRUNCATE | STATEMENT | EXECUTE FUNCTION qe.qe_forbid_stage_outcome_mutation() |
| qe | qe_stage_outcome | trg_qe_stage_outcome_no_update | BEFORE | UPDATE | ROW | EXECUTE FUNCTION qe.qe_forbid_stage_outcome_mutation() |
