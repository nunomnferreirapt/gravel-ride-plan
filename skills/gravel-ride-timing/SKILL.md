---
name: gravel-ride-timing
description: Find the best day and time window for a gravel ride from weather, air quality, pollen, UV and daylight data.
---

# Gravel Ride Timing Advisor

## STEP 1: Load user preferences

Read the user's preferences from `~/.claude/skills/gravel-ride-timing/preferences.md` (in this skill's folder).

These are **soft preferences**, not hard blocks. Rank days by overall comfort; do not reject days outright.

## STEP 2: Determine location and dates

- If the user specifies a city, use it. Otherwise use the home base from `preferences.md`.
- If the user says "this weekend", resolve to the upcoming Saturday and Sunday dates.
- If the user specifies a ride duration (for example "3 hours"), use it to evaluate which time windows are long enough.

## STEP 3: Geocode the location

Use `mcp__geocoding-mcp__geocode_city` to get latitude and longitude. Reuse the result if the same city was already geocoded in this conversation.

## STEP 4: Pull all data in parallel

Fire ALL of these MCP calls at once (they are independent):

1. `mcp__sun-weather-mcp__get_weather_forecast`: `days` large enough to cover all requested dates
2. `mcp__sun-weather-mcp__get_sunrise_sunset_range`: start_date and end_date for the requested days
3. `mcp__air-quality-mcp__get_air_quality_forecast`: enough days to cover the requested dates
4. `mcp__air-quality-mcp__get_uv_index`: same range
5. `mcp__air-quality-mcp__get_pollen_forecast`: same range (max 5 days)

Do NOT use web search. The MCP servers are the sole data source.

## STEP 5: PASS 1, daily overview (pick the day)

For each candidate day, extract a quick summary:
- Feels-like range (min to max)
- Wind average, gusts and direction
- Precipitation total and probability
- Cloud cover %
- Air quality (European AQI peak and rating)
- UV index and risk level
- Pollen (dominant type and level)
- Sunrise and sunset

Present a **comparison table** with all candidate days side by side. Rank days by overall ride comfort (weighing rain, wind, temperature, sun). Give a clear **verdict**: best day, why in 2 or 3 bullets, and any caveats.

No hard filters. Flag discomfort factors ("heavy rain", "extreme gusts") but do not reject days. The user decides.

### PASS 1 OUTPUT FORMAT

```
| Metric | Day 1 | Day 2 | ... |
|--------|-------|-------|-----|
| ...    | ...   | ...   | ... |

### Verdict: [Best day]
- [reason 1]
- [reason 2]
- [caveat if any]
```

## STEP 6: PASS 2, hourly detail (find the window)

After recommending the best day, fetch hourly weather for that day with the script in this skill:

```bash
uv run ~/.claude/skills/gravel-ride-timing/scripts/hourly_weather.py \
  --lat <latitude> --lon <longitude> --date <YYYY-MM-DD> --start-hour 7 --end-hour 20
```

From the hourly data, identify the **best ride window** (2 to 4 hours) based on:
- Driest stretch (lowest precipitation and probability)
- Warmest feels-like
- Calmest wind
- Most sun (lowest cloud cover)

Present the hourly data for the recommended window, plus a 1 hour buffer on each side:

```
### Best window: [Day] [Start] to [End] ([duration] h)

| Time | Feels-like | Wind | Gusts | Cloud | Rain | Rain % |
|------|-----------|------|-------|-------|------|--------|
| ...  | ...       | ...  | ...   | ...   | ...  | ...    |

[1 or 2 lines on why this window]
```

If the user already stated a preference for which day, skip Pass 1 and go straight to Pass 2 for that day.

## STEP 7: Check events and offer next steps

After presenting the timing verdict, run `/gravel-ride-events` for the evaluated date range without asking. This shows organized rides and community group rides that align with the weather window. Prioritize gravel events (`"gravel": true`).

Then offer:

> **"Want me to build a gravel route, or check what gear to bring?"**

- Route: invoke `/gravel-route-builder` (location and date context carry over)
- Gear: invoke `/gravel-ride-gear` with the weather data from this run
- The user may also ask for both, or skip
