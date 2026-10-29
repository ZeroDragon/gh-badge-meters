# Dev Levels

A status-battery app for the [GitHub Universe badge](https://github.com/badger/home)
(MonaOS / Badgeware, 2026). It generalizes the shipped *social battery* concept
into multiple meters, each with an optional auto-decay "cadence".

## Screens

Five screens, cycled with **LEFT / RIGHT** (wraps around):

1. **Social Battery** — energy for chatting
2. **Coffee Level** — caffeine meter
3. **Rest Level** — rest meter
4. **Overview** — the three batteries side by side as vertical bars
   (chat / coffee cup / crescent moon icons), all levels at a glance
5. **Fork Me** — QR code linking to this repo, scan it to fork

Each level uses the same 4-color band palette; at **10% or less** the lit
cell blinks red/off on every screen.

## Controls (screens 1–3)

| Button | Action |
| --- | --- |
| UP / DOWN | Level +10% / −10% |
| SELECT | Cycle cadence 0 → 1 → … → 10 → 0 |

## Cadence

The cadence is the number of **hours** a battery takes to drain to 0:

- `0` — no decay (level only changes manually)
- `1` — empty in 1 hour (−10% every 6 minutes)
- `10` — empty in 10 hours (−10% every 60 minutes)

Decay is computed from persisted timestamps, so it keeps running while the
app is closed. Manually adjusting a level **or** changing its cadence resets
that battery's decay timer.

## Installing

Copy the app folder to the badge's `/system` partition as
`/system/apps/devlvls/` (the menu discovers any `apps/<dir>/` with an
`__init__.py`), or paste `__init__.py` into the
[developer simulator](https://badger.github.io/simulator/) to try it in the
browser. State persists via Badgeware's `State` store under the `devlvls` key.

## Credits

Layout and mood concept based on the `social_battery` app by
@dylan-mccarthy. MIT licensed like the upstream repo.
