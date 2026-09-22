# Alpine Ski Resort Dataset 2026/27 — Build Report

Built on 2026-09-22 by the research agent from the brief "Alpine Ski Resort Dataset 2026/27 — Research Agent Brief".
This document records everything that was done, every methodological decision, the QA results and the known limitations,
so that the workbook can be audited and refreshed next season.

## 1. Deliverables

| File | Content |
|---|---|
| `alpine_ski_resorts_2026_27.xlsx` | Workbook with sheets `resorts` (214 rows × 24 columns), `notes` (8 bullets), `qa` (counts, low-confidence rows, exclusions) |
| `resorts.csv` | Flat export of the `resorts` sheet (UTF-8, ISO dates, driving hours to two decimals) |
| `candidates.csv` | Master candidate list before enrichment (215 rows, with inclusion basis, batch, skiresort.com cross-check URL) |
| `inputs/` | Full pipeline: scripts, agent brief, per-batch inputs and outputs, routing results, overrides, validation report |

Workbook formatting: header row bold and frozen, autofilter on, `opening_date_2026_27` as real Excel dates (`TBD` as text),
all numeric fields as numbers, column widths set. Rows sorted by country (FR, IT, AT, CH, DE, SI) then opening date ascending with
`TBD` last.

## 2. Final QA summary

| Metric | Value |
|---|---|
| Rows | 214 (FR 69, IT 41, AT 57, CH 45, DE 2, SI 0) |
| Type | Glacier 9 · Glacier + non-glacier 27 · Non-glacier 178 |
| Opening status | confirmed_2026_27 173 · estimated_from_2025_26 38 · year_round_glacier 2 · TBD 1 |
| Share confirmed vs estimated (of those two) | 82.0 % confirmed |
| Price status | published_2026_27 131 · estimated_from_2025_26 78 · blank 5 |
| Webcams | 188 unique URLs, 188 returned HTTP 200 at build time, 0 blank |
| Confidence | high 26 · medium 169 · low 19 |
| Routes forced around a closed pass | 31 |
| Excluded after research | 1 (Dachstein Glacier) |
| Duplicate `resort_name` + `country` | 0 |

Validation checks passed: every date parses or is `TBD` and matches its status; `max_elevation_m` within 1,000–4,000; `piste_km` > 0;
scores are multiples of 0.5 in 0–5; currency matches country (CHF only for CH); every webcam URL returned 200.

## 3. Workflow as executed

### 3.1 Environment
- Python 3.12 with openpyxl, pandas, requests. HTTPS from Python required `truststore.inject_into_ssl()` (corporate proxy root
  certificate) and `PYTHONUTF8=1` for console output.
- Web access via WebSearch/WebFetch for research; OSRM public demo server for routing; Nominatim for a coordinate fallback.

### 3.2 Candidate discovery (`inputs/build_candidates.py`, `inputs/skiresort_scrape.csv`)
- Scraped all 1,158 Alpine entries from skiresort.com (ranking pages by slope length and by top altitude, plus the glacier list):
  name, country, region, base/top elevation, piste km, lifts, day price.
- Filtered with the four inclusion criteria: ≥ 60 km on the standard local day pass, lift-served glacier skiing, FWT/FWQ venue or
  consistently cited freeride/ski-touring destination, top lift ≥ 2,800 m. FWT/FWQ venue history checked against
  freerideworldtour.com (Verbier, Fieberbrunn, Chamonix, Val Thorens, Kappl, Kühtai, Nendaz, Obergurgl, Crans-Montana, Leysin, etc.).
- Applied the row-granularity rule (one row per destination with its own base village, own lift base and own marketing):
  3 Vallées → 6 rows (Courchevel, Méribel, Les Menuires, Val Thorens, Saint-Martin-de-Belleville, Orelle); Paradiski → 3;
  Espace Killy → 2; Portes du Soleil → Morzine, Avoriaz, Les Gets, Châtel, Champéry, Morgins; Grand Massif → 4; Sybelles → 4;
  Espace Diamant → 3; Ski Arlberg → 3; SkiWelt → 6; Skicircus → 3; Silvretta Arena → Ischgl + Samnaun; Zillertal Arena → 3;
  Snow Space Salzburg → 3; 4 Vallées → Verbier, Nendaz, Veysonnaz, Thyon; Engadin → St. Moritz, Corvatsch, Diavolezza;
  Dolomiti Superski → one row per valley area exactly as listed in the brief; Zermatt and Cervinia as two rows.
  Villages of one resort (Courchevel 1850/1650/1550/Le Praz, Serre Chevalier's four villages, Val Cenis, Dévoluy, Hochkönig,
  Serfaus-Fiss-Ladis, Laax/Flims/Falera) stay on one row.
- Result: 215 candidates (FR 69, AT 58, CH 45, IT 41, DE 2, SI 0), inside the expected 180–260 range.
- Slovenia: no lift-served area meets any criterion (Krvavec 30 km / 1,971 m, Kanin–Sella Nevea 30 km / 2,293 m, Vogel 22 km,
  Kranjska Gora 20 km, Mariborsko Pohorje 35 km). Reported as considered and excluded rather than padded.
- Germany qualifies only through the Zugspitze glacier area (Garmisch-Partenkirchen) and the Oberstdorf–Kleinwalsertal two-country
  day pass (~130 km); Kleinwalsertal is the matching Austrian row.

### 3.3 Enrichment (`inputs/agent_brief.md`, `inputs/lists/`, `inputs/enrich_*.csv`)
- Eleven parallel sub-agents, one per batch of 16–25 resorts (FR1–FR4, IT1–IT2, AT1–AT3 incl. the two Bavarian rows, CH1–CH2),
  each following the same written brief: official lift-company/resort sites first, skiresort.com for cross-checks, bergfex/feratel/
  roundshot for webcams; never invent a value, blank plus comment instead.
- Per resort they returned: actual first lift day of 2025/26, any published 2026/27 date, source note, highest lift-served point,
  piste km with the pass it refers to, adult one-day peak-window price with min/max, price status, road head, base-parking
  coordinates, proposed freeride and touring scores with evidence, verified webcam URL, comments, sources, confidence.
- The coordinator reviewed every batch report, filled gaps and corrected inconsistencies through `inputs/overrides.csv`
  (67 lines, each with a reason): e.g. Méribel 2026/27 price 71.20 EUR and 150 km, Courchevel 150 km, Pointe de la Masse 2,804 m
  for Les Menuires/Saint-Martin, Kaunertal's cancelled 26 Sep 2026 opening, Kirchberg's own Fleckalmbahn date, Printse-pass
  elevation (2,700 m) for Nendaz/Veysonnaz/Thyon, Swiss dynamic-price ranges, six score calibrations.

### 3.4 Opening dates and prices (rules applied in `inputs/assemble.py`)
- Published 2026/27 date from the operator or tourist office → `confirmed_2026_27`. Dated pre-opening weekends count as the first
  day; the continuous opening is given in comments.
- Otherwise the actual 2025/26 first day shifted by +364 days (same weekday in 2026) → `estimated_from_2025_26`.
- 2026/27 dates that only appear on aggregators (skiresort.com, bergfex, skiinfo) or in provisional press round-ups
  (alti-mag, Parcs & Loisirs) are not treated as confirmed: when a 2025/26 date exists, the shifted date is used and the provisional
  date is noted in comments (12 rows); when no 2025/26 date exists either, the aggregator date is used and confidence set to low
  (Andermatt, Sedrun, Disentis, Laax, St. Moritz, Obersaxen).
- Year-round glaciers: Hintertux (2026-10-03, start of 2026/27 winter tariff) and Zermatt (2026-11-01) → `year_round_glacier`.
- `TBD` only for Passo dello Stelvio (summer/autumn-only glacier, 30 May–1 Nov 2026, road closed in winter).
- Prices: adult one-day pass in the peak window, local pass rather than mega-pass (basis in comments); published 2026/27 tariff →
  `published_2026_27`, else 2025/26 peak price → `estimated_from_2025_26`. Dynamic pricing: lower bound = documented peak-Saturday
  price (Blick's 24 Jan 2026 comparison, or the operator's "from" price), upper bound = list/window price, "dynamic pricing" in
  comments. Five dynamic-pricing resorts publish no usable figure and are blank: Gargellen, Heiligenblut, Adelboden, Lenk, Savognin.
- Vialattea's four rows were downgraded to estimated because vialattea.it blocked automated access and the 2026/27 date was inferred
  from tariff periods only.

### 3.5 Driving from Milan (`inputs/route_milan.py`, `inputs/geocode_fallback.py`, `inputs/routes.csv`)
- Tool: OSRM public demo server (car profile, OpenStreetMap data), because no Google Maps API key was available. Origin Piazza del
  Duomo (45.4642, 9.1900). OSRM has no traffic model, so its free-flow time is equivalent to the 06:00 weekday departure.
- Destination = agent-supplied coordinates of the main base parking, or the road head for car-free resorts (Täsch for Zermatt,
  Lauterbrunnen for Wengen, Stechelberg for Mürren, Fiesch valley station for Aletsch Arena, Wiler for Lauchernalp, Blatten for
  Belalp). One coordinate was corrected by the coordinator (Mölltal Glacier → Innerfragant valley station).
- Winter closures enforced by checking the route geometry against closed-pass summit coordinates (radius 1.2 km, tightened to
  0.3–0.8 km where a tunnel runs under the pass: Great St Bernard, San Bernardino, Lombarde, Madeleine; two-point rules where a
  resort sits at the pass: Nassfeld/Pramollo Italian ramp, Allos, Joux Verte). When all OSRM alternatives crossed a closed pass, the
  fastest clean route through pass-specific detour points or country gateway points was taken (31 rows), and the detour is noted
  in comments.
- Closed set = the brief's list (Stelvio, Gavia, Umbrail, Great St Bernard pass, Furka, Grimsel, Susten, Nufenen, Oberalp, Klausen,
  Splügen, San Bernardino pass, Flüela, Albula, Galibier, Iseran, Petit St Bernard, Bonette, Cayolle, Agnel, Lombarde, Timmelsjoch,
  Silvretta, Grossglockner) plus standard winter closures (Gotthard pass, Lukmanier, Forcola di Livigno, Izoard, Mont Cenis,
  Colombière, Joux Plane, Croix de Fer, Glandon, Madeleine, Cormet de Roselend, Sarenne, Allos, Champs, Couillole, Noyer,
  Penser Joch, Fedaia, Manghen, Finestre, Colle San Carlo, Pfitscher Joch, Staller Sattel, Pramollo from Pontebba, Sölk,
  Col de la Croix, Sanetsch, Bassachaux, Joux Verte, Passo delle Erbe, Duran, Hahntennjoch, Pragel, Glaubenberg/Glaubenbielen,
  Lech–Warth road). Tunnels and passes listed as open in the brief were left available. Passo dello Stelvio's own summit was
  exempted for its row (summer access via Bormio).
- Typical forced detours: Tarentaise resorts via Albertville (Petit St Bernard closed), Sölden/Obergurgl/Vent via Innsbruck
  (Timmelsjoch), Isola 2000 and Auron via Nice (Lombarde), Sedrun/Disentis via Chur (Oberalp/Lukmanier), Jungfrau resorts and
  Meiringen via Lucerne (Susten/Grimsel), Warth via Bregenzerwald (Lech–Warth road), Nassfeld via Villach (Pramollo ramp),
  Livigno via Bormio (Forcola), Val Cenis/Bonneval via Fréjus (Mont Cenis), Vaujany/Oz via Bourg-d'Oisans (Glandon).
- Two false positives were found and fixed during testing: a road-name check (access roads are often named after the pass they lead
  to, e.g. "Route du Col de la Croix de Fer" through Saint-Sorlin) was removed, and an inaccurate Furkajoch coordinate that flagged
  Damüls was dropped from the list. Car-train segments would have been flagged from OSRM step modes; none were used in the final
  routes.

### 3.6 Scores and calibration (`inputs/calibrate.py`)
- Agents proposed 0–5 half-step scores with evidence (FWT/FWQ history, guidebook off-piste itineraries, Camptocamp/Gulliver route
  density, Haute Route, guide offices), following the brief's rubric and anchor resorts.
- Coordinator calibration: all anchor resorts checked (freeride 5.0: Chamonix, Verbier, Zermatt, Val d'Isère, La Grave, Engelberg,
  St. Anton; 4.5: Tignes, Andermatt, Alagna, Courmayeur, Lech–Zürs, Fieberbrunn, Disentis; 4.0: Sölden, Saas-Fee, Davos, Les Arcs,
  Alpe d'Huez, Arabba; touring 5.0: Chamonix, Zermatt, Verbier, Engelberg, Andermatt; 4.5: Saas-Fee, Tignes, Val d'Isère,
  Courmayeur, Grindelwald, Corvatsch/Sils; 4.0: Davos, St. Moritz, Les 2 Alpes, Ischgl, Kühtai, Dolomites valleys; 3.5: Obergurgl,
  Sölden) — all matched. Six adjustments for consistency: Axamer Lizum, Bad Gastein, Gargellen, Heiligenblut, Saalbach freeride
  4.0 → 3.5; Galtür touring 4.5 → 4.0.
- Final distribution — freeride: 5.0 ×7, 4.5 ×7, 4.0 ×27, 3.5 ×70, 3.0 ×71, ≤2.5 ×32; touring: 5.0 ×5, 4.5 ×11, 4.0 ×37,
  3.5 ×77, ≤3.0 ×84.

### 3.7 Validation and workbook (`inputs/assemble.py`, `inputs/validation_report.txt`)
- Merged the 11 enrichment files, applied overrides, computed dates/statuses, merged routing, re-verified every webcam URL with a
  browser user agent (3 attempts, 45 s timeout), ran the validation checks listed in section 2, sorted, and wrote the workbook,
  `resorts.csv`, `work/assembled_debug.csv` (with internal fields) and `work/excluded.csv`.

## 4. Judgement calls to be aware of
- **La Plagne** typed Non-glacier (3,080 m): the Bellecôte glacier lifts were dismantled in 2023 and the new gondola tops out on rock.
- **Passo Tonale** typed Glacier per the brief's example (Presena), although most of its 100 km is non-glacier.
- **Chamonix 3,842 m and Courmayeur 3,466 m**: Aiguille du Midi and Punta Helbronner are lift-served glacier access for off-piste
  only (Vallée Blanche); pistes top out at 2,765 m and 2,755 m. Comments say so.
- **Plose** kept although its local pass is ~42 km, because the brief names it explicitly as a Dolomiti Superski row.
- **Borderline criterion-3/4 inclusions**, all commented: Vals, Grächen, Molines/Saint-Véran (2,830 m), Bonneval-sur-Arc, Vent,
  Galtür, Kappl, Axamer Lizum, Sainte-Foy-Tarentaise, Arêches-Beaufort, Gargellen, Macugnaga (lift status uncertain after the
  December 2025 Monte Moro accident; low confidence).
- **Village-level opening dates** for linked areas (Kirchberg, Pinzolo, Saint-Martin, etc.); area-wide dates kept only where the
  early-opening sector is marketed as the resort's own start (Kitzbühel/Resterkogel).
- **Piste km** follow the pass a visitor actually buys: local pass where it exists (Val Thorens 150, Verbier 203, Printse 220,
  Disentis 60), linked-area pass where only that exists (Sybelles 275, SkiWelt 275, Zillertal Arena 150, Portes du Soleil 600 for
  Champéry/Morgins). The basis is stated in comments.

## 5. Low-confidence rows (19)
Méribel, Valberg, Villard-de-Lans–Corrençon (FR); Macugnaga (IT); Kaunertal Glacier, Gargellen, Heiligenblut (AT); Andermatt,
Sedrun, Disentis, Laax, St. Moritz, Corvatsch, Obersaxen–Mundaun, Adelboden, Lenk, Savognin, Leysin, Belalp (CH).
Reasons per row are in the `comments` column and on the `qa` sheet: dynamic pricing without a published peak price, 2026/27 dates
known only from aggregator season entries, official sites blocked or script-only, or unresolved lift status.

## 6. Resorts considered and excluded
- **After research:** Dachstein Glacier (Ramsau) — glacier ski lifts dismantled in March 2023; only cross-country, touring and a
  cable car remain.
- **At candidate stage (fail all criteria or excluded by the brief):** all Slovenian areas (Krvavec, Kanin–Sella Nevea, Vogel,
  Kranjska Gora, Mariborsko Pohorje, Cerkno); Brides-les-Bains (brief's 3 Vallées example), Les Houches, Pralognan-la-Vanoise,
  Aussois, Les Marécottes; Chiesa in Valmalenco, Aprica, Limone Piemonte, Speikboden/Klausberg, Gitschberg-Jochtal, Carezza,
  Paganella, Piancavallo, Tarvisio; Innsbruck Nordkette, Hinterstoder, Kals–Matrei, Ankogel, See, Golm, Brandnertal, Zauchensee,
  Turracher Höhe, Dachstein West; Elm, Anzère, Melchsee-Frutt, Hoch-Ybrig, Sörenberg, Pizol, Wildhaus, Airolo and other Ticino
  areas, Bourg-St-Pierre/Super Saint-Bernard (closed), Bernina Heliski and Valpelline–Ollomont (heliski only); Bavarian hills
  (Sudelfeld, Brauneck, Balderschwang, Oberjoch, Winklmoos).

## 7. Known limitations
- Most 2026/27 prices and some dates were not yet published in late September 2026; 38 dates and 78 prices are 2025/26 estimates.
- OSRM free-flow times run roughly 10–20 % slower than Google Maps on mountain roads; distances are to a base parking or road head
  with ~100–300 m coordinate precision.
- Piste-km figures follow the lift companies' own claims, which exceed independently measured lengths for several areas.
- Webcam URLs were verified for HTTP 200 only; some official pages are script-rendered.
- Scores are calibrated judgements, not measurements.
- The sub-agents' web-search quota ran out mid-task in every batch; the remaining research was done by fetching official pages,
  aggregators and press directly, which is reflected in the confidence column.

## 8. How to refresh next season
1. Re-run the eleven enrichment agents with `work/agent_brief.md` and `work/lists/list_*.csv` (update the season labels).
2. `python geocode_fallback.py` → `routes_in.csv`; `python route_milan.py routes_in.csv routes.csv` (cached rows are reused when
   coordinates are unchanged).
3. Review `python calibrate.py`; put corrections in `work/overrides.csv` (`id, field, value, reason`; fields may also be
   `comments_append`, `score_notes_append`, `sources_append`).
4. `python assemble.py` (add `--no-webcam-check` for dry runs) → workbook, `resorts.csv`, `validation_report.txt`.

## 9. File inventory (`work/`)
`build_candidates.py`, `skiresort_scrape.csv`, `agent_brief.md`, `lists/list_*.csv`, `enrich_FR1..FR4/IT1..IT2/AT1..AT3/CH1..CH2.csv`,
`geocode_fallback.py`, `routes_in.csv`, `route_milan.py`, `routes.csv`, `route_log_*.txt`, `rebuild_routes.py`, `overrides.csv`,
`calibrate.py`, `assemble.py`, `assembled_debug.csv`, `excluded.csv`, `validation_report.txt`.
