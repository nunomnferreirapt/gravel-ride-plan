---
name: gravel-ride-plan
description: Plan a gravel ride near Amsterdam end to end: timing, events, route, gear, briefing. Use for "plan a ride" requests.
---

# Plan a gravel ride (guided flow)

Present each step and ask before invoking it. The user may skip or reorder steps.

1. **When to ride**: `/gravel-ride-timing`. Its last step runs `/gravel-ride-events` automatically, so events on the recommended day appear here without a separate step.
2. **Where to ride**: if the `komoot-mcp` server is registered (its tools start with `mcp__komoot-mcp__`), `/gravel-route-builder`, to build or recommend a route, or to join a found event. If it is not, do not run the route builder: ask for the route the user has in mind (start, distance, rough surface) or take the found event's route, and continue.
3. **What to bring**: `/gravel-ride-gear` for the chosen day's conditions.
4. **Ride briefing**: once the first three are decided, offer: "Want a ride briefing?"

After each step, summarize the result and ask "Ready for the next step?".

### Ride briefing (final step)

If the user says yes, produce a concise summary:

1. Fetch hourly weather for the ride window:
   `uv run ~/.claude/skills/gravel-ride-timing/scripts/hourly_weather.py --lat <lat> --lon <lon> --date <YYYY-MM-DD> --start-hour <h> --end-hour <h>`
2. Combine with the chosen route details (distance, surface, key waypoints).
3. Map gear to hourly conditions and flag when to add or remove layers.

Output format:

```
## Ride Briefing: [Day, Date] [Start] to [End]

**Route:** [name or description], [distance] km, [surface type]
**Start:** [location] at [time]

| Time  | Feels-like | Wind   | Cloud | UV  | Gear change                                   |
|-------|------------|--------|-------|-----|-----------------------------------------------|
| 12:00 | 9 C        | 8 ENE  | 0%    | 3.8 | Start: full stack (merino, jersey, vest)      |
| 13:00 | 11 C       | 10 ENE | 0%    | 4.1 | Pocket the vest if warming up                 |
| 14:00 | 11 C       | 10 ENE | 0%    | 4.0 | none                                          |
| 15:00 | 12 C       | 8 ENE  | 0%    | 3.5 | Sunscreen reapply (UV above 3)                |

**Pack:** [items to bring based on conditions throughout]
**Gaps:** [any missing gear needed]
```

Preferences: the timing, gear and route skills read `~/.claude/skills/gravel-ride-timing/preferences.md` (soft preferences, not hard blocks). Edit that file once after installing.
