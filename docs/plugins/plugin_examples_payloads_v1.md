# ✅ Fichier réécrit — `docs/plugins/plugin_examples_payloads.md`

````markdown id="ex9m2c"
# Plugin Example Payloads — v1
Non-authoritative examples of runtime payloads

Status: REFERENCE (Non-Canonical)
Scope: Illustration only

Authoritative contracts:
- docs/contracts/runtime_schema_v1.md
- docs/contracts/scoreEntry_contract_v1.md
- docs/contracts/runtime_plugin_io_v1.md

This document contains examples only.
If a contradiction appears, contracts prevail.

---

# 1. Example — QCM StageOutcome

Example of a resolved multiple-choice stage.

```json
{
  "schema_version": "v1",
  "stage_id": "stage_1",
  "plugin_key": "qcm",
  "finished_at": "2024-01-01T12:00:00Z",
  "public_state": {
    "question": "What is 2 + 2?",
    "correct_index": 1,
    "stats": {
      "0": 2,
      "1": 5,
      "2": 1
    }
  },
  "private_state": {
    "correct_index": 1
  },
  "score_entries": [
    {
      "schema_version": "v1",
      "player_id": "p1",
      "delta_score": 10,
      "grade_value": 1,
      "grade_max": 1,
      "reason": "correct_answer"
    },
    {
      "schema_version": "v1",
      "player_id": "p2",
      "delta_score": 0,
      "grade_value": 0,
      "grade_max": 1,
      "reason": "wrong_answer"
    }
  ],
  "metadata": null
}
````

Notes:

* All scoring values are integers.
* No ranking included.
* No percentage included.
* Engine aggregates mechanically.

---

# 2. Example — Informational Plugin (No Scoring)

Example of a stage that only displays content.

```json
{
  "schema_version": "v1",
  "stage_id": "stage_2",
  "plugin_key": "info_slide",
  "finished_at": "2024-01-01T12:05:00Z",
  "public_state": {
    "title": "Historical Context",
    "content": "This event happened in 1789..."
  },
  "private_state": null,
  "score_entries": null,
  "metadata": null
}
```

No scoring produced.

---

# 3. Example — WebSocket STAGE_STARTED

```json
{
  "type": "STAGE_STARTED",
  "payload": {
    "stage_id": "stage_1",
    "plugin_key": "qcm",
    "public_state": {
      "question": "What is 2 + 2?",
      "choices": ["3", "4", "5"]
    }
  }
}
```

---

# 4. Example — WebSocket PLAYER_ACTION

```json
{
  "type": "PLAYER_ACTION",
  "payload": {
    "stage_id": "stage_1",
    "action": {
      "selected_index": 1
    }
  }
}
```

Engine forwards action without interpretation.

---

# 5. Example — WebSocket STAGE_RESOLVED

```json
{
  "type": "STAGE_RESOLVED",
  "payload": {
    "stage_id": "stage_1",
    "public_state": {
      "correct_index": 1
    },
    "score_entries": [
      {
        "schema_version": "v1",
        "player_id": "p1",
        "delta_score": 10,
        "grade_value": 1,
        "grade_max": 1,
        "reason": "correct_answer"
      }
    ]
  }
}
```

---

# 6. Example — HOST_SNAPSHOT

```json
{
  "type": "HOST_SNAPSHOT",
  "payload": {
    "player_totals": {
      "p1": {
        "total_score": 30,
        "total_grade_value": 3,
        "total_grade_max": 3
      },
      "p2": {
        "total_score": 10,
        "total_grade_value": 1,
        "total_grade_max": 3
      }
    },
    "stage_index": 2
  }
}
```

Notes:

* Totals are pure summations.
* No ranking.
* No sorting implied.

---

# 7. What These Examples Do NOT Imply

These examples do not:

* Define ranking behavior
* Define winner selection
* Define scoring formulas
* Define UI structure
* Define timing rules

They illustrate structure only.

Contracts remain authoritative.
