---
name: gravel-ride-events
description: Find gravel events and group rides near Amsterdam for a date range (Battistrada, Maats.cc, Ride Out Amsterdam).
---

# Gravel Ride Events Finder

## STEP 1: Run the scraper

```bash
uv run ~/.claude/skills/gravel-ride-events/scripts/scrape_events.py \
  --start YYYY-MM-DD --end YYYY-MM-DD
```

- If chained from `/gravel-ride-timing`, use the dates from the recommended ride window
- If standalone, ask the user for a date range (default: upcoming weekend)
- Add `--all-locations` to include events outside the Amsterdam 1 hour drive radius
- JSON to stdout, progress to stderr

## STEP 2: Present results

### Scheduled events
Show as a table, gravel events first (flagged with `"gravel": true`). Add a type column:

| Date | Event | Type | Location | Distance | Price | Link |
|------|-------|------|----------|----------|-------|------|

- Events with `"gravel": true`: show as **Gravel** (bold)
- Events with `"gravel_only": true`: show as **Gravel only**
- Mixed events (gravel plus road or mtb): show the string from the `"type"` field
- Non-gravel events: show type or "Road/Mixed"
- Battistrada includes full type info (for example "gravel, road - cyclosportive, ride")

### Recurring community rides
List events with `"recurring": true` separately. These happen weekly or biweekly from Maats stores. Suggest checking the link for the exact schedule.

### No results
If empty, say so and suggest checking the source sites directly.

## STEP 3: Highlight best matches

When chained from `/gravel-ride-timing`:
- Highlight events on the **recommended ride day**
- Flag Amsterdam-based events or nearby starting points
- Note if a Maats recurring ride aligns with the weather window

When standalone:
- Sort by proximity to Amsterdam
- Note gravel-specific versus mixed events

## Sources

1. **Battistrada**: NL gravel calendar, server-rendered HTML (most comprehensive)
2. **Maats.cc**: Shopify JSON API, community rides and organized events
3. **Ride Out Amsterdam**: WordPress, Amsterdam group rides

Not scraped (they need a headless browser): Gravel Calendar (Bubble.io), City Alps (Wix).
