# Alpine Ski Resorts 2026/27

A single-page, mobile-first guide to 214 major Alpine ski resorts in France, Italy, Austria,
Switzerland and Germany: opening dates, day-pass prices, driving time from Milan, freeride and
ski-touring scores, and one-tap links to Google Maps, driving directions, the official weather
service, the regional avalanche bulletin and the resort webcam.

**Live site:** https://gcarassai.github.io/ski_bums/

Plain HTML, CSS and JavaScript. No build step, no framework, no analytics, no third-party
requests at runtime. Hosted for free on GitHub Pages.

## Repository layout

```
index.html                  the page
css/app.css                 styles (light and dark themes)
js/app.js                   application code (filters, sorting, URL state, detail panel)
sw.js                       service worker: offline fallback, always network-first
assets/                     logo, favicons, home-screen icons, web app manifest
data/resorts.json           the dataset the site reads (generated, do not edit by hand)
data/meta.json              row count, data date, season, sample flag (generated)
data/coordinates.csv        latitude/longitude per resort (merged in by the converter)
data/region_links.csv       official weather + avalanche bulletin URLs per country/region
scripts/xlsx_to_json.py     workbook -> data/*.json converter with validation
scripts/make_icons.py       regenerates logo and icons from one source image
alpine_ski_resorts_2026_27.xlsx   the source workbook
.github/workflows/          Pages deployment and data validation
```

## Updating the data

1. Edit the `resorts` sheet of `alpine_ski_resorts_2026_27.xlsx` (keep the column headers).
2. Regenerate the JSON:

   ```
   pip install openpyxl            # once
   python scripts/xlsx_to_json.py alpine_ski_resorts_2026_27.xlsx
   ```

   The script validates every row (enums, numbers, dates, URLs, score steps, currency vs
   country) and refuses to write anything if a cell is wrong. It prints one line per problem
   with the row number and resort name, and exits with code 1. Fix the cells and run again.

3. Commit and push:

   ```
   git add alpine_ski_resorts_2026_27.xlsx data/
   git commit -m "Update resort data"
   git push
   ```

The push triggers the **Deploy to GitHub Pages** action, which publishes the repository root
as-is. The site is usually updated within one to two minutes. The service worker fetches the
data from the network first on every load, so a reload shows the new data immediately; the
cached copy is only used when offline.

A second action, **Validate data**, runs the converter in check mode on every push and fails
if the workbook has invalid cells or if `data/resorts.json` was not regenerated after a
workbook change.

### Coordinates, weather and avalanche links

The workbook does not contain `latitude`, `longitude`, `weather_url` or `avalanche_url`
columns, so the converter merges them from two sidecar files:

- `data/coordinates.csv` — one row per resort (`resort_name,country,latitude,longitude`),
  the main base lift or road head. A resort without a row is a validation error: add its
  coordinates when you add a resort.
- `data/region_links.csv` — one row per `country,region` with the official weather page and
  avalanche bulletin for that region, plus a `*` row per country as a fallback. Every URL was
  fetched and checked at build time. Edit a row here to change the link for a whole region.

If you add any of these four columns to the workbook, non-blank workbook cells take
precedence over the sidecar files, so per-resort links can be introduced gradually.

### Sample data

`python scripts/xlsx_to_json.py workbook.xlsx --sample` marks the output as sample data;
the site then shows a yellow banner above the filters.

## Replacing the logo

Replace **`assets/logo.png`** (the header logo, any aspect ratio, about 160 px tall).
To also refresh the favicon and home-screen icons from the same image, run:

```
pip install pillow            # once
python scripts/make_icons.py path/to/your-logo.png
```

This rewrites `assets/logo.png`, `favicon-32.png`, `favicon-48.png`, `apple-touch-icon.png`,
`icon-192.png`, `icon-512.png` and `icon-maskable-512.png`. Commit and push.

## Running locally

```
python -m http.server 8000
```

Then open http://localhost:8000/ . Any static server works; the page must be served over
HTTP (not opened as a file) because it fetches `data/*.json`.

## Custom domain (optional)

1. Create a file named `CNAME` in the repository root containing the bare domain,
   e.g. `ski.example.com`, and push it.
2. At your DNS provider add a `CNAME` record for `ski` pointing to `gcarassai.github.io`.
   For an apex domain (`example.com`) add `A` records to `185.199.108.153`,
   `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (and matching `AAAA` records
   if you want IPv6).
3. In the repository, Settings → Pages → Custom domain, enter the domain and tick
   **Enforce HTTPS** once the certificate is issued (a few minutes).

## Sharing a view

Every filter, the sort order, the search text and the open resort are in the URL. Use the
**Copy link** button, or bookmark the page, to return to the exact same view. A resort can be
deep-linked with `?resort=zermatt`.

## Data provenance

The dataset was researched in September 2026. Dates and prices marked "~" are estimates carried
over from the 2025/26 season. See `BUILD_REPORT.md` for the research method, QA results and
known limitations, and the `notes` and `qa` sheets in the workbook.
