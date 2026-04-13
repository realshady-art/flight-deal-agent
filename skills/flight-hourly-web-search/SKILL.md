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
