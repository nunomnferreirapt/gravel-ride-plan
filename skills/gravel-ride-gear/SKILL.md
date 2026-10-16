---
name: gravel-ride-gear
description: Recommend gear and clothing for a gravel ride from the forecast. Use for what-to-wear or kit questions.
---

# Gravel Ride Gear Advisor

## STEP 1: Load the gear inventory

Read `references/gear-inventory.md` (relative to this skill). It lists every item the user owns, and marks what they do NOT have as `NONE`. Only recommend items from this inventory. When conditions call for an item marked `NONE`, flag it as a **gap**.

## STEP 2: Get weather data

If weather data for the target ride is already in the conversation (from `/gravel-ride-timing`), reuse it. Otherwise:
1. Read `~/.claude/skills/gravel-ride-timing/preferences.md` for the home base
2. Geocode the location with `mcp__geocoding-mcp__geocode_city`
3. Pull weather with `mcp__sun-weather-mcp__get_weather_forecast`
4. Pull UV with `mcp__air-quality-mcp__get_uv_index`

## STEP 3: Determine conditions for the ride window

Extract for the specific ride time window:
- Feels-like temperature (minimum during the ride)
- Wind speed and gusts
- Precipitation probability
- Cloud cover
- UV index

## STEP 4: Recommend gear from the inventory

Match conditions to the user's items by category. Temperatures are feels-like, in Celsius.

### Head
- Above 15: helmet only
- 8 to 15: buff or cap as headband under the helmet
- Below 8: buff pulled up over neck and ears, or a thermal cap, under the helmet

### Upper body
- Above 18: light sleeveless or short-sleeve baselayer and a short-sleeve jersey
- 14 to 18: light baselayer and a long-sleeve jersey
- 10 to 14: merino long-sleeve baselayer, long-sleeve jersey and a wind vest
- 6 to 10: the same full stack; pack a jacket if available
- Below 6: thermal or winter jacket over the stack
- Gusts above 35 km/h: add the wind vest
- Rain probability above 30%: rain jacket

### Lower body
- Above 12: bib shorts
- 5 to 12: bib shorts with leg or knee warmers
- Below 5: thermal tights
- Variable 10 to 16 days: arm warmers to pocket later

### Hands
- Above 15: none, or short-finger gloves
- 5 to 15: full-finger gloves
- Below 5: insulated gloves
- Rain: waterproof gloves

### Feet
- Above 10: regular socks
- Below 10: merino or thermal socks, and overshoes or toe covers
- Rain or wet ground: waterproof overshoes

### Extras
- One bidon is enough for rides under 2 hours or below 15; otherwise two
- UV index above 3: remind sunscreen
- Gusts above 40 km/h: suggest postponing (exposed dike paths)

## STEP 5: Output

```
### Conditions: [feels-like] C, wind [speed] km/h gusts [gusts], [rain status], [cloud or sun]

**Wear:**
- Head: [item from inventory]
- Upper: [items from inventory]
- Lower: [item from inventory]
- Hands: [item from inventory, or "none needed"]
- Feet: [item from inventory]

**Pack in pocket:**
- [items to bring but not wear at the start, such as the vest or buff]

**Gaps for these conditions:**
- [missing gear the rules called for, with a specific purchase suggestion]
```

If no gaps apply, omit the Gaps section. Keep it concise; the user is an experienced cyclist.

## Chain to route builder

After presenting gear recommendations, if the user does not already have a route, offer:

> **"Want me to build a gravel route for this ride?"**

If yes, invoke `/gravel-route-builder` (the location context carries over).
