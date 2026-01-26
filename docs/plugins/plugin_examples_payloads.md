# Payload Examples (plugin-owned)

These examples show typical shapes for PlayerEvent.payload and PluginFrame.payload.
They are conventions, not requirements.

---

## PlayerEvent.payload examples

### Yes/No
{ "answer": true }

### MCQ single
{ "selected": ["A"] }

### MCQ multi (choose many)
{ "selected": ["A", "C"] }

### Slider discrete/continuous/log
{ "value": 1907 }

### Free text
{ "text": "This image makes me think of..." }

### Wordcloud (single word)
{ "word": "adventure" }

### Ordering (drag & drop order)
{ "order": ["w3", "w1", "w2"] }

### Association (left -> right mapping)
{
  "pairs": [
    { "left_id": "l1", "right_id": "r2" },
    { "left_id": "l2", "right_id": "r1" }
  ]
}

---

## PluginFrame.payload examples

### Live tally for MCQ (Mentimeter-like)
{
  "prompt": { "title": "Your question..." },
  "choices": [
    { "id": "A", "label": "Option A", "count": 12 },
    { "id": "B", "label": "Option B", "count": 5 }
  ],
  "total_responses": 17
}

### Gauge / positioning
{
  "scale": ["yes", "almost", "neutral", "almost_no", "no"],
  "distribution": [3, 6, 10, 4, 2]
}

### Wordcloud summary
{
  "words": [
    { "text": "adventure", "weight": 12 },
    { "text": "campfire", "weight": 9 }
  ]
}

### Podium
{
  "podium": [
    { "player_id": "p1", "score": 1200 },
    { "player_id": "p7", "score": 1150 },
    { "player_id": "p3", "score": 900 }
  ]
}

---

## StageOutcome examples

### No-score stage (slide/wordcloud/scoreboard)
{
  "score_deltas": null,
  "grade_deltas": null,
  "render_summary": { "words": [ ... ] },
  "plugin_state_out": null
}

### QCM with grade + Kahoot-like score
{
  "score_deltas": [
    { "player_id": "p1", "delta_score": 850, "meta": { "rank": 2, "time_ms": 1200 } }
  ],
  "grade_deltas": [
    { "player_id": "p1", "value": 1, "max_value": 1, "scale": "points" }
  ],
  "render_summary": { "correct_choice": "B" }
}
