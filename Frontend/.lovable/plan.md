# Funnel page: filters below the graph, visual cards on the right

## Layout change

- The cohort filter moves out of the right rail and becomes a horizontal bar directly beneath the funnel diagram (under the carousel dots), using the existing `FilterBar` "bar" variant so the funnel stays the uncontested hero.
- The right rail (300px, widened to ~320px) becomes a stack of small graph cards — every card leads with a visual, with the number as support.

## The five rail cards (top to bottom)

1. **Closed-won ARR + sparkline** — hero card keeps the big figure, gains a small area/line sparkline of ARR won per week across the window, with the maturity zone dimmed (same convention as /trends).
2. **Outcome ring** — a slim donut ring splitting the cohort's deals into won / lost / open (counts from `derivePosture`), win rate printed in the ring's center. Replaces the separate "Win rate" and "Deals opened" text tiles.
3. **Open pipeline by stage** — mini horizontal bars: open ARR sitting in each deal stage (discovery → negotiation), iterating `DEAL_STAGES` config as always. Replaces the flat "Open pipeline ARR" tile and previews where the money is stuck.
4. **Won ARR by segment** — mini horizontal bars from the existing `cohortStats(deals, "segment")`, using the categorical palette. Replaces "Median won ACV" (which moves into this card's caption).
5. **Bridge between the funnels** — upgraded from text to a small two-bar visual: SQOs with vs. without a deal record, plus the no-lineage side-inflow bar, all from the existing `lineageBridge`.

Each card keeps the eyebrow-label style and gets an entry in the explainer registry so "how this is computed" stays accurate.

## Technical notes

- Two small additions to `src/lib/rf/engine.ts` (the only place numbers are derived): `wonArrByWeek(deals, filters)` for the sparkline and `openArrByStage(deals)` for the stage bars, each with a matching `postureExplainer()` registry entry. Everything else reuses existing derivations (`derivePosture`, `cohortStats`, `lineageBridge`).
- New `src/components/rf/PostureCards.tsx` renders the five cards with hand-rolled SVG (sparkline, ring, bars) — no charting library, consistent with `Chart.tsx`. Components render only; no inline computation.
- `src/routes/index.tsx` re-arranges the grid: funnel + filter bar in the left column, card stack right. On mobile the cards flow in a 2-up grid under the filter bar.
- No changes to derivation logic, filters semantics, or the funnel diagram itself.
