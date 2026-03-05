# MCQ Plugin — Multiple Choice Question

---

# I — Core Plugin Contract

## 1. Plugin Identity

* **Name**: `mcq`
* **Type**: `quiz`
* **Architecture**: Standalone plugin discovered by `quiz-engine`
* **Engine Role**: Orchestrates lifecycle and WebSocket routing
* **Plugin Role**: Owns all game intelligence, scoring logic, bots behavior, state machine, and UI state

The engine is unaware of scoring rules.
The plugin computes and applies score deltas.

---

## 2. Configuration — `mcq.ini`

Location: `quiz_engine/plugins/mcq/mcq.ini`

```ini
[mcq]
default_time_limit_s = 30
allowed_time_limits_s = 0,15,30,60,120

default_points = 1000
min_points = 10
max_points = 100000

default_choices_count = 4
min_choices = 1
max_choices = 20

choice_columns_smartphone = 2
choice_columns_tablet = 4
choice_columns_desktop = 6

default_player_choice_view = compact
allow_player_toggle_choice_view = true

[mcq.modes]
enabled_modes = oneclick,multianswer,influence,influence_bots,influence_bots_nice,influence_bots_evil

[mcq.bots]
min_bots = 10
bots_vote_early_ratio = 0.80
early_time_window_ratio = 0.20
bots_good_answer_ratio_nice = 0.80
bots_good_answer_ratio_evil = 0.20
```

### 2.1 Configuration Rules

* `enabled_modes` MUST control which modes are selectable in authoring.
* `min_points` MUST be `10`.
* `default_choices_count` MUST be within `[min_choices, max_choices]`.
* `min_choices` MUST be `>= 1`.
* At question creation, `default_choices_count` answer fields MUST be pre-created.
* Authoring MUST allow add/remove answers only within `[min_choices, max_choices]`.
* Compact-grid columns are plugin-configurable via:
  * `choice_columns_smartphone`
  * `choice_columns_tablet`
  * `choice_columns_desktop`
* Disabled modes MUST NOT be available for new questions.
* Existing questions using a disabled mode MUST become read-only.
* `time_limit_s = 0` means no automatic end; host MUST terminate the question.
* Toggle state MUST reset between questions.
* Configuration is strictly plugin-local.

---

## 3. Question Data Schema

Each MCQ question MUST follow:

```json
{
  "type": "quiz",
  "plugin": "mcq",
  "title": "string",
  "prompt": "string",
  "mode": "oneclick | multianswer | influence | influence_bots | influence_bots_nice | influence_bots_evil",
  "time_limit_s": "integer",
  "points": "integer",
  "examination": "boolean",
  "choices": [
    {
      "id": "string",
      "label": "string",
      "is_correct": "boolean",
      "weight": "integer"
    }
  ]
}
```

### 3.1 Schema Rules

* `title` and `prompt` MUST be non-empty.
* `mode` MUST exist in `enabled_modes`.
* `points` MUST be within `[min_points, max_points]`.
* `time_limit_s` MUST be in `allowed_time_limits_s`.
* Choices count MUST be within `[min_choices, max_choices]`.
* For `multianswer`:

  * `weight` MUST be present.
  * `is_correct` MUST NOT be used.
  * Correctness is derived from `weight > 0`.
* For all other modes:

  * `is_correct` MUST be present.
  * `weight` MUST NOT be used.

---

## 4. Game Phases (Deterministic State Machine)

The plugin MUST implement:

1. `LOBBY_WAIT`
2. `QUESTION_INTRO`
3. `ANSWERING`
4. `RESULTS`
5. `DONE`

Transitions:

* `LOBBY_WAIT → QUESTION_INTRO`
* `QUESTION_INTRO → ANSWERING`
* `ANSWERING → RESULTS`

  * timer expiration OR
  * host termination
* `RESULTS → DONE`
* `DONE → engine handoff`

### 4.1 Pre-start Countdown (Engine-provided)

The `LOBBY_WAIT` phase MAY include an engine-provided countdown (e.g., "next question starts in N seconds").

- If a countdown is provided by the engine, host and players MUST display it.
- If no countdown is provided, host and players MUST display a waiting state without countdown.

---

## 5. Scoring Model

### 5.1 Global Formula

```
final_score = question_points × mode_value × time_factor
```

Where:

* `question_points = question.points`
* `mode_value` depends on mode
* `time_factor = 1 - (elapsed_time / total_time)`

Constraints:

* At start: `time_factor = 1`
* At end of timer: `time_factor` approaches 0
* If `time_limit_s = 0`, then `time_factor = 1`
* Player earned points MUST always be integers in `Z` (negative, `0`, or positive), never decimal values.
* Scores MAY be negative

---

## 6. Game Modes

### 6.1 oneclick

* Player selects one choice.
* Selection immediately submits and locks.
* `mode_value = 1` if correct, else `0`.

---

### 6.2 multianswer

* Player may select multiple choices.
* Submit button required.
* Raw score:

```
raw = sum(weight of selected choices)
```

* `mode_value = raw`
* Raw MAY be negative.

---

### 6.3 influence

* Player selects one choice.
* Selection submits immediately.
* Player MAY change selection until question ends.
* Host displays anonymous marbles (one per player).
* Latest selection at phase end determines scoring.

Scoring identical to `oneclick`.

---

### 6.4 influence_bots

Same as `influence`, plus bots.

Bot rules:

* `bot_count = max(min_bots, player_count)`
* Bots indistinguishable from players.
* 80% of bots vote within first 20% of time.
* Remaining bots vote randomly.
* If all players voted early:

  * Remaining bots vote immediately.
* Bots answers random.

---

### 6.5 influence_bots_nice

Same as `influence_bots`
Probability of correct answer = 80%

---

### 6.6 influence_bots_evil

Same as `influence_bots`
Probability of correct answer = 20%

---

## 7. Examination Mode

If `examination = true`:

* Player MUST NOT see:

  * correctness feedback
  * earned score
* Host MAY see aggregated statistics
* Leaderboard SHOULD be disabled

If `false`:

* Player sees correctness and earned score
* Host MAY display leaderboard

---

# II — Interfaces Specification

## 8. Authoring Interface

The authoring UI MUST allow full creation/editing of MCQ questions.

### Fields

* Title (required)
* Prompt (required)
* Mode (from enabled_modes)
* Points (default from config)
* Timer (from allowed list)
* Examination (checkbox)

### Choices

* Add / remove / reorder
* Each choice MUST have stable `id`
* At creation, authoring MUST initialize `default_choices_count` choices
* Add/remove MUST be constrained by `[min_choices, max_choices]`
* Mode rules:

  * If `multianswer`: show `weight`, hide `is_correct`
  * Otherwise: show `is_correct`, hide `weight`

Validation MUST prevent invalid save.

---

## 9. Presenter Interface (Host)

### Common Header

Host MUST display:

* Title
* Prompt
* Player count
* Timer (or “No timer”)
* End Question button

### LOBBY_WAIT

Host MUST display:

- A waiting state ("Waiting for next question…")
- Connected player count
- If the engine provides a pre-start countdown: "Starting in Ns"

### QUESTION_INTRO

* Title + prompt
* Full labeled answers
* Timer

### ANSWERING

* Full labeled answers
* Live response count
* Histogram (optional)
* Influence modes:

  * Marble stack at right
  * Live marble movement

### RESULTS

* Correct answers highlighted
* Final distribution
* If not examination: leaderboard MAY appear

---

## 10. Player Interface (Responsive)

Mobile-first.

### Common

* Title
* Prompt (may be visually reduced in compact mode)
* Timer status

### LOBBY_WAIT

Player MUST display:

- A waiting state ("Waiting for next question…")
- If the engine provides a pre-start countdown: "Starting in Ns"

### QUESTION_INTRO

* Title + prompt
* No interaction

### ANSWERING

Two display modes:

#### Compact (default)

* Buttons show index only
* Smartphone columns = `choice_columns_smartphone` (default: `2`)
* Tablet columns = `choice_columns_tablet` (default: `4`)
* Desktop columns = `choice_columns_desktop` (default: `6`)
* Prompt MAY be visually minimized
* Answer grid MUST dominate layout

#### Label Mode

* Buttons show full label
* Smartphone: 1 column
* Tablet: 2 columns
* Desktop: 2–3 columns

Toggle:

* Allowed if config enables
* Reset every question

Interaction:

* `oneclick`: lock after selection
* `multianswer`: submit button required
* `influence*`: selection change allowed until end

### RESULTS

If not examination:

* Show correctness
* Show earned score

If examination:

* Do not show correctness or score

---

# III — Communication Contract

## 11. WebSocket Contract

All messages MUST follow:

```json
{
  "type": "EVENT_NAME",
  "payload": {}
}
```

### Incoming

* `MCQ_PLAYER_SELECT`
* `MCQ_PLAYER_SUBMIT`
* `MCQ_HOST_END`

### Outgoing

* `MCQ_STATE_UPDATE`
* `MCQ_LIVE_STATS`
* `MCQ_RESULTS`
* `PLUGIN_DONE`

---

## 12. Engine Handoff

At `DONE`, plugin MUST emit:

```json
{
  "type": "PLUGIN_DONE",
  "payload": {
    "question_id": "...",
    "score_deltas": {
      "player_id": integer
    },
    "statistics": {}
  }
}
```

After emission, plugin relinquishes control to engine.

---
