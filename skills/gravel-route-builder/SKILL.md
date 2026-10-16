---
name: gravel-route-builder
description: Find gravel routes on Komoot by distance, start point, surface and scenery. Use for route-planning requests.
---

# Gravel Route Builder

Needs the `komoot-mcp` server (https://github.com/nunomnferreirapt/komoot-mcp) and `geocoding-mcp`. Preferences come from `~/.claude/skills/gravel-ride-timing/preferences.md`.

## MODE SELECTION

Determine the user's intent:
- **"find", "recommend", "suggest" a route**: go to STEP 1 (recommendation flow)
- **"build", "combine", "create", "mix", "merge" a route from segments**: go to STEP 0C (combination flow)

If unclear, ask: "Do you want me to recommend an existing route, or build a new one by combining the best gravel segments from your saved tours?"

---

## COMBINATION FLOW (Steps 0C to 5C)

### STEP 0C: Pre-flight questions

Before doing any work, ask the user the following. Present them as a compact checklist and wait for answers. Use the defaults from `preferences.md` if the user says "defaults" or "usual".

> To build your route I need a few details:
>
> 1. **Route type**: loop (back to start) or point-to-point (different start and end)?
> 2. **Starting point**: where do you want to start?
>    - _Exact (an address) or flexible ("anywhere within 20 min drive")?_
>    - _If flexible: how far are you willing to drive? (default from preferences: 60 min, about 50 km)_
> 3. **End point** _(only if point-to-point)_: where do you want to finish? Exact or flexible, as above.
> 4. **Distance or time**: how long should the route be?
>    - _Distance in km, or a total time budget including driving (driving time is subtracted). Average speed from preferences, default 18 km/h._
> 5. **Route name** _(optional)_: or one is generated with the prefix "Gravel-AI".

**Do NOT proceed until the user answers.** If the user already gave some of these in the initial request, confirm what you understood and ask only for the missing details.

### STEP 1C: Load preferences and resolve constraints

Read `~/.claude/skills/gravel-ride-timing/preferences.md`.

Resolve constraints from step 0C:
- **Route type:** loop (default) or point-to-point.
- **Starting point:** geocode via `mcp__geocoding-mcp__geocode_city` if needed. Default: the home base in preferences (for Amsterdam: lat 52.3676, lon 4.9041).
- **Start flexibility:** "exact" uses that point as the route start. "flexible" uses the driving radius to pick a start closer to gravel (for example Weesp for a 20 min drive from Amsterdam).
- **End point** _(point-to-point only)_: geocode if needed, same exact or flexible logic.
- **Search radius:** flexible start, from driving time (60 min = 50 km, 30 min = 25 km). Exact start, radius_km = 25.
- **Target distance:** from user input or default 50 km. If a total time was given, subtract driving time and convert the rest at the average speed.
- **Min gravel %:** default 60.
- **Route name:** user-provided or `Gravel-AI [area name] [distance]km`.

**Point-to-point:** pass both start and end coordinates to `build_combined_route`. The combiner selects tour sections that make forward progress along the start-to-end corridor and fills gaps with OSRM connectors. For loops, omit the end point.

### STEP 2C: Find source tours

Use `mcp__komoot-mcp__list_tours` to find tours near the starting point. Do NOT filter by sport_type (many gravel routes are classified as mtb_easy). Fire both calls in parallel:
1. Planned tours: tour_type="tour_planned", near_lat, near_lon, radius_km=50, limit=50
2. Recorded tours: tour_type="tour_recorded", near_lat, near_lon, radius_km=50, limit=50

**Important:** only planned tours have surface segment data. Recorded tours are skipped by the combiner.

Collect all tour IDs. If the user specified tours, use those instead.

### STEP 3C: Build the combined route

Call `mcp__komoot-mcp__build_combined_route` with:
- tour_ids: all collected tour IDs (or the user's subset)
- start_lat, start_lon from step 1C (and end_lat, end_lon for point-to-point)
- distance_km and min_gravel_pct from the constraints
- route_name
- save_path: `<routes folder>/built-routes/<route-name>.gpx`, routes folder from preferences

### STEP 4C: Present results

```
### Combined Route: [Name]
- **Distance:** X km | **Gravel:** Y% (Z km)
- **Road connectors:** X km (Y%)
- **Saved highlights visited:** [names, if any]
- **Source tours used:** [tour names]
- **Segments used:** N from saved tours, M road connectors
- **GPX saved to:** [path] (a second file, [name]-waypoints.gpx, holds the waypoint list for the Komoot planner)
```

The combiner fetches the user's saved Komoot highlights and gives tour sections near them a scoring bonus, so the route prefers scenic spots the user bookmarked.

Ask: **"Want me to upload this to Komoot? I can also adjust the distance or gravel target and rebuild."**

To upload: `mcp__komoot-mcp__upload_gpx_to_komoot` with the saved GPX file.

### STEP 5C: Chain to timing and gear (optional)

After the route is final, offer:

> **"Want me to also find the best day and time to ride this route, and what gear to bring?"**

If yes, invoke `/gravel-ride-timing` with the route's starting coordinates, then `/gravel-ride-gear` with the resulting weather data.

---

## RECOMMENDATION FLOW (Steps 1 to 8)

## STEP 1: Load user preferences

Read `~/.claude/skills/gravel-ride-timing/preferences.md`. Defaults it provides: home base, maximum driving time to the start, surface priority, decision factors.

## STEP 2: Parse user constraints

Extract from the request (preferences supply the defaults):

| Constraint | Default | Example |
|---|---|---|
| Starting point | home base | "near Hilversum", "starting from Utrecht" |
| Distance | 40 to 60 km | "about 50 km", "short ride" (30 km), "long ride" (80 km or more) |
| Time budget | convert to distance at the average speed | "3 hours" is about 54 km at 18 km/h |
| Min gravel % | 60% | "mostly gravel", "at least 70% gravel" |
| Max driving time to start | 60 min | "within 30 min drive" |
| Preferred tags | none | "forest", "dike", "scenic", "flat" |

"Short ride": 25 to 35 km. "Medium ride": 40 to 60 km. "Long ride": 70 to 100 km.

## STEP 3: Geocode the starting point

Use `mcp__geocoding-mcp__geocode_city`. For the home base, use the coordinates in preferences without geocoding.

Search radius: 60 min driving is about 50 km, 30 min about 25 km.

## STEP 4: Query Komoot in parallel

Fire ALL of these at once:

1. `mcp__komoot-mcp__list_tours`: sport_type="touringbicycle", tour_type="tour_planned", near_lat, near_lon, radius_km from step 3
2. `mcp__komoot-mcp__list_tours`: sport_type="touringbicycle", tour_type="tour_recorded", near_lat, near_lon
3. `mcp__komoot-mcp__get_highlights`: lat, lon, radius_m=15000 (scenic points in the area)

## STEP 5: Fetch detailed data for top candidates

For the most promising tours (up to 10), call `mcp__komoot-mcp__get_tour_details` for each tour_id in parallel. This gives the surface breakdown (gravel, asphalt, dirt) and way types (path, cycleway, road).

## STEP 6: Score and rank

```
score = (gravel_pct x 0.40)
      + (highlight_density x 0.20)
      + (distance_fit x 0.20)
      + (scenic_tags x 0.10)
      + (elevation_variety x 0.10)
```

- **gravel_pct**: share of gravel and unpaved surface (from Komoot surfaces)
- **highlight_density**: Komoot highlights within 2 km of the route, normalized
- **distance_fit**: 1.0 at the target distance, lower as it deviates
- **scenic_tags**: bonus for matching preferred tags
- **elevation_variety**: gentle changes preferred over flat, normalized 0 to 1

**Hard filters:** distance within 30% of target; start within the driving radius; gravel plus unpaved at or above min_gravel_pct.

## STEP 7: Present the top 5 routes

```
### Route 1: [Name]
- **Distance:** X km | **Gravel:** Y% | **Elevation:** +Z m / -W m
- **Surface:** X km gravel, Y km paved, Z km dirt
- **Start:** [location] (about X min drive from home)
- **Highlights:** [nearby highlights]
- **Tags:** [if any]

### Route 2: [Name]
...
```

Then ask: **"Want me to download the GPX for any of these? I can save it to the routes folder and optionally upload it to Komoot."**

## STEP 8: On user selection

1. `mcp__komoot-mcp__download_tour_gpx` with `save_path=<routes folder>/built-routes/[name]-[date].gpx`
2. If requested, `mcp__komoot-mcp__upload_gpx_to_komoot` with the GPX file
3. Report the file path and the Komoot URL

## NOTES

- Do NOT use web search for route data. The Komoot MCP server is the sole data source.
- If no Komoot credentials are set up, tell the user to set `KOMOOT_EMAIL` and `KOMOOT_PASSWORD` for the server or run its `setup_credentials` tool.
- Surface data from Komoot is authoritative (it comes from OpenStreetMap).

## ITERATIVE IMPROVEMENT: DIFF BEFORE YOU BUILD

Routes folder from preferences (default `~/gravel/routes/`):
- `built-routes/`: generated GPX files
- `adjusted-routes/`: the user's manual corrections (`YYYY-MM-DD_[komoot-tour-id]_[route-name].gpx`)
- `diff-reports/`: one diff analysis per adjusted route (`YYYY-MM-DD_[route-slug].md`)

Before working on a combined route, check for new manual corrections:

1. Scan `adjusted-routes/` for files
2. Scan `diff-reports/` for existing diffs
3. If an adjusted route has no matching diff report, run a GPX diff against its built version first and save the findings to `diff-reports/`
4. Read the latest diff report before building; its fix priorities override older assumptions

After generating a route, remind the user: "Upload this to Komoot, adjust as needed, and save the corrected GPX to `adjusted-routes/`. I will diff it next time to keep improving."
