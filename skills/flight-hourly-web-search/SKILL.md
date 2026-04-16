---
name: flight-hourly-web-search
description: Search current low-fare flights from a configured origin to a configured destination scope using web search only. Use for the flight-deal-agent hourly terminal/dashboard workflow when the result must avoid paid APIs and browser automation, and return a structured top-N list with links and a short narrative summary.
---

# Flight Hourly Web Search

Use this skill only for the local flight monitor workflow.

## Hard constraints

- Use web search only.
- Do not call paid flight APIs.
- Do not use browser automation, Browser Use, or scripted browsing.
- Work from currently indexed/public web results only.
- Prefer directly linked fare/result pages or credible fare aggregation pages.

## Search goal

Given:
- one or more `origin_airports`
- one `destination_scope`
- one `top_n`

Find the best currently visible low-fare options you can verify from public search results.

## Origin coverage rules

- Treat `origin_airports` as a required search set, not a hint.
- You must actively search across every listed origin airport. Do not silently collapse the job to the first airport only.
- When public results support it, include at least one credible finding for each listed origin before filling the remaining slots with the globally cheapest options.
- If one origin genuinely has no useful indexed fares, say that explicitly in the summary instead of pretending it was covered.

## Ranking logic

1. Prefer lower price.
2. Prefer round-trip over one-way when both are available.
3. Prefer concrete date ranges over vague marketing copy.
4. Prefer fresher or more directly attributable sources.
5. Drop results that have no usable source URL.
6. Keep searching until you have a credible Top N set when public results support it; do not stop at 3-5 items just because you found a few cheap fares early.

## Destination mix (longer / US-forward)

The board is most useful when it surfaces **longer, transborder value**, not only trips that are cheap because they are very short.

- **Prioritize US destinations** that are **farther from the origin** than the immediate Pacific Northwest / BC–Alberta corridor when public results support it—for example U.S. East Coast, Florida, Texas, the Southwest, Chicago-area hubs, and other **mid-continent or cross-country** markets—provided the fare is still credible and well-sourced.
- **Deprioritize** filling most of the Top N with **ultra-short hops** whose low price is “normal” (e.g. adjacent Canadian cities, routine YVR/YYC/YYJ/YYF-style short haul, or border-adjacent US airports like BLI unless the deal is clearly exceptional vs. typical pricing).
- When both a nearby cheap route and a **more distant US** option are verifiable, **prefer including the longer US option** in the list so the user sees variety beyond short-haul defaults.
- Still obey **origin coverage**: every listed `origin_airport` should get a fair search; this rule only affects **which destinations you emphasize** when ranking and choosing among similarly credible results.
- If `destination_scope` includes Canada, you may still include standout Canadian long-haul, but **do not let the entire list collapse to only the closest Canadian cities** when US results are available.

## Output contract

You must output a fenced `json` block first, then a short human-readable summary.

The JSON object must match this shape:

```json
{
  "headline": "One-line snapshot of this hour",
  "summary": "Short summary of whether this hour has anything meaningfully cheap",
  "findings": [
    {
      "route": "YVR -> YYC",
      "origin_airport": "YVR",
      "destination_airport": "YYC",
      "price_display": "CA$81 round trip",
      "price_value": 81,
      "currency": "CAD",
      "date_range": "Apr 23-28",
      "source_name": "Google Flights",
      "source_url": "https://...",
      "note": "Why this fare is worth noticing"
    }
  ]
}
```

## Output rules

- Target `top_n` findings whenever public web results can support that many credible entries.
- Return fewer findings only when the current web results genuinely do not provide enough verifiable options; never invent entries.
- `price_value` should be numeric when reasonably inferable, otherwise `null`.
- `destination_airport` should be IATA when clear; otherwise use the city/airport token that is actually visible.
- `note` should stay short and factual.
- The summary should briefly mention origin coverage, especially when one origin produced no credible fares.
- After the JSON block, add a compact Markdown summary suitable for a terminal transcript.
