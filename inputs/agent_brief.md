# Enrichment brief for ski-resort research sub-agents

You are a data-research sub-agent. You enrich a fixed list of Alpine ski resorts for a structured
dataset (winter 2026/27). Today is 2026-09-22. You never invent facts. Blank plus a comment beats a guess.

## Input / output
- Input list: `lists/list_<BATCH>.csv` in this folder (columns: id, batch, resort_name, local_name, country,
  region, ski_area, inclusion_basis, road_head_hint, skiresort_url, notes_for_agent). Do NOT rename, merge,
  split or drop resorts. Keep `id`, `resort_name`, `country`, `region`, `ski_area` exactly as given (you may
  fix an obvious typo and say so in your report). If `notes_for_agent` says "VERIFY … may EXCLUDE", research it
  and, if it fails the inclusion criteria, still output the row but put `EXCLUDE: <reason>` at the start of
  `comments`.
- Output: `enrich_<BATCH>.csv` in this folder, UTF-8, comma-separated, header row exactly as below, one row per
  input resort. Write the file incrementally (append each finished row, flush) so nothing is lost if you stop early.
- Tools: WebSearch, WebFetch, and Bash with Python 3.12 (requests, pandas available). In Python always start with
  `import truststore; truststore.inject_into_ssl()` (corporate proxy) and run with env `PYTHONUTF8=1`.
  Budget roughly 3–6 web lookups per resort. Prefer: official resort/lift-company site → skiresort.com resort page
  (elevation, km, price cross-check) → bergfex/feratel/roundshot for webcams.

## Output columns (exact order)
1. `id` – from input.
2. `resort_name` – from input.
3. `local_name` – from input; fill only if materially different from resort_name (e.g. Gröden, Sulden, Breuil-Cervinia).
4. `country` – from input (FR, IT, AT, CH, DE).
5. `region` – from input.
6. `ski_area` – from input (you may refine wording, keep meaning).
7. `type` – `Glacier`, `Glacier + non-glacier`, or `Non-glacier`.
   - `Glacier`: early-season and core identity is glacier skiing; non-glacier terrain minor/absent
     (Hintertux, Stubai, Kaunertal, Pitztal, Mölltal, Kitzsteinhorn, Stelvio, Passo Tonale/Presena, Dachstein, Val Senales).
   - `Glacier + non-glacier`: lift-served glacier terrain exists but most of the area is non-glacier
     (Zermatt, Cervinia, Saas-Fee, Tignes, Val d'Isère, Les 2 Alpes, Sölden, Engelberg, Verbier, Laax, Corvatsch,
     Crans-Montana, Alpe d'Huez, Val Thorens, La Plagne, Monterosa/Alagna, Arabba–Marmolada, Chamonix, Courmayeur).
   - `Non-glacier`: no lift-served glacier terrain.
8. `opening_2025_26_actual` – YYYY-MM-DD: the actual first day lifts ran for skiing in season 2025/26 (autumn 2025).
   Source: official site news/season dates page, press, skiresort.com "season" info, bergfex. Blank if not found.
9. `opening_2026_27_published` – YYYY-MM-DD if the resort has already published a 2026/27 opening date; else blank.
10. `opening_source_note` – ≤ 15 words: where the date came from (e.g. "official season-dates page", "2025 press release").
11. `max_elevation_m` – integer, highest lift-served skiable point in metres (official site or skiresort.com).
12. `piste_km` – integer, marked pistes on the standard local day pass (the pass a visitor actually buys at that
    resort; e.g. Val Thorens local pass, not full 3 Vallées; for Dolomiti Superski valleys the valley pass;
    for Sybelles/SkiWelt/Zillertal Arena etc. where only the full linked pass exists, use the linked-area km).
13. `piste_km_basis` – ≤ 12 words: which pass the km refers to.
14. `ticket_price_min` – number: lower bound of adult one-day pass in the peak window (Christmas–New Year / February
    half-terms), standard online/window price. If a single fixed price, same value in min and max.
15. `ticket_price_max` – number: upper bound.
16. `currency` – EUR (FR, IT, AT, DE) or CHF (CH).
17. `price_status` – `published_2026_27` if the 2026/27 price is published; else `estimated_from_2025_26` (using the
    2025/26 peak price). Use the local pass (see 12). Say "dynamic pricing" in comments when applicable.
18. `road_head` – for car-free resorts, the village where the car journey ends (Täsch for Zermatt, Lauterbrunnen for
    Wengen/Mürren, valley cable-car station for Aletsch Arena etc.). Blank if you can drive to the resort's main base.
19. `base_lat`, 20. `base_lon` – decimal degrees (5 decimals) of the main base parking / valley lift station where a
    visitor's car journey ends (= the road_head if one is given). Take from OpenStreetMap/Nominatim, Google Maps or the
    resort's access page. This drives the Milan routing, so be precise about the correct village.
21. `freeride_score_0_5` – proposed 0–5 in half steps, rubric:
    5.0 world-class, globally recognised (Chamonix, Verbier, Zermatt, Val d'Isère, La Grave, Engelberg, St. Anton);
    4.5 top-tier lift-accessed off-piste with strong guiding scene (Tignes, Andermatt, Alagna–Monterosa, Courmayeur,
    Lech–Zürs, Fieberbrunn, Disentis); 4.0 strong off-piste, often glacier/large-resort based (Sölden, Saas-Fee, Davos,
    Les Arcs, Alpe d'Huez, Arabba–Marmolada); 3.5 good but limited/less known; ≤3.0 mainly on-piste/beginner.
    Evidence: FWT/FWQ venue history, freeride guidebooks, documented off-piste itineraries.
22. `ski_touring_score_0_5` – proposed 0–5 in half steps, rubric: 5.0 world-class hub with high-alpine multi-day
    classics and deep guide culture (Chamonix, Zermatt, Verbier, Engelberg, Andermatt); 4.5 extensive graded day tours,
    reliable snow, good access (Saas-Fee, Tignes/Val d'Isère, Courmayeur, Grindelwald, Sils/Bernina); 4.0 many
    documented day tours and decent infrastructure (Davos, St. Moritz, Les 2 Alpes, Ischgl, Dolomites valleys, Kühtai);
    3.5 good local touring, less variety (Obergurgl, Sölden, most Austrian glaciers); ≤3.0 limited.
    Evidence: Camptocamp/Gulliver route density, SAC/CAI/ÖAV/FFCAM guidebooks, guide-office offerings, Haute Route.
23. `score_notes` – one sentence justifying both scores with evidence (e.g. "FWT stop; Vallée Blanche; huge touring culture").
24. `webcam_url` – verified live URL of the resort's main webcam page (official site preferred, else bergfex /
    skiline / feratel / roundshot). Prefer multi-cam pages. It MUST return HTTP 200 when you check it with Python
    requests (GET, allow redirects, browser User-Agent). Blank if none verified. Never guess.
25. `webcam_http_status` – the status code you observed (e.g. 200).
26. `comments` – short factual notes: winter pass closures on the direct route from Italy, year-round/autumn glacier
    operation, price caveats, dynamic pricing, anything unusual. Start with `EXCLUDE: …` only if the resort fails inclusion.
27. `sources` – all URLs used for this row separated by ` | ` (at least the official site and one cross-check).
28. `confidence` – `high` (all key fields – date, elevation, km, price – from official sources), `medium` (one or more
    estimated / from aggregators), `low` (several fields estimated or conflicting sources).

## Rules
- Dates: report the raw 2025/26 actual date and any published 2026/27 date; the coordinator computes the final
  2026/27 field. Glaciers that ski year-round (Hintertux, Zermatt): put the published start of the 2026/27 winter
  product if any in column 9, and note "year-round" in comments.
- Prices: adult, one day, peak window, local pass. Numbers only, no currency symbols.
- Never fabricate a date, price, elevation or URL. Use blank + comment.
- Keep `comments` factual and short. Reasoning about scores goes in `score_notes` only.
- Language: English (except local_name).
- CSV hygiene: quote fields containing commas; no line breaks inside fields; decimal point, not comma.

## Final report (your last message)
Summarise: rows written, rows with blank date / blank price / blank webcam, any `EXCLUDE:` rows with reason,
anything the coordinator must double-check (conflicting sources, unusual pass structures), and the file path.
