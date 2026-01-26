# Determinism & Random Seed

## Rule
Plugins must be deterministic for replay and fairness.

If a plugin uses randomness (bots, noise, randomized prompt/choices):
- StageDefinition.random_seed MUST be present.
- All randomness must be derived from that seed only.

## Recommended approach
- Initialize RNG once per stage runtime using the seed.
- Do not use system time or global random state.
- Do not call external services that change results.

## Bots (Chaos plugin)
- Bot actions must be derived from seed + stable ids (player_id/stage_id) for reproducibility.
- If you simulate distributions (gaussian, etc.), the generated sequence must be reproducible.

## Timing-based scoring
- Use PlayerEvent.server_received_at for all timing calculations.
- Ignore client clock for fairness (client_sent_at is informational only).
