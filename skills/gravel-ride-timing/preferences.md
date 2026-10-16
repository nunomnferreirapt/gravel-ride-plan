---
name: Gravel ride preferences
description: Rider comfort thresholds, home base, route preferences and folders. Read by the timing, gear and route skills.
---

# Gravel ride preferences

Edit this file after installing. Everything here is a soft preference the skills weigh, not a hard block. The defaults describe a rider based in Amsterdam.

## Rider
- Home base: Amsterdam, NL (default start; approximate center 52.3676, 4.9041). Replace with your own town or address.
- Maximum drive to a start point: 60 min (about 50 km)
- Average riding speed, used to turn a time budget into a distance: 18 km/h

## Comfort
- Rain: prefer none; light rain under 1 mm is acceptable
- Temperature: warmer is better, no minimum; cold-weather kit is listed in the gear inventory
- Wind: lower is always better; it matters most on exposed polders and dikes

## Routes
- Maximize the share of compacted gravel; target at least 60% unpaved
- Decision factors, in order: surface type, distance, start point, gravel highlights, scenery
- When time allows, drive 20 to 25 min to start closer to the good gravel instead of riding urban kilometers
- Route source: Komoot, through the komoot-mcp server; final routes are uploaded back to Komoot for navigation
- Routes folder: `~/gravel/routes/` with `built-routes/`, `adjusted-routes/` and `diff-reports/` (see gravel-route-builder)

## Gear
- Inventory: `~/.claude/skills/gravel-ride-gear/references/gear-inventory.md` is the source of truth; the gear skill reads it at run time
