#!/usr/bin/env python3
"""Convert the ski-resort workbook into the JSON files the website reads.

Usage:
    python scripts/xlsx_to_json.py path/to/alpine_ski_resorts_2026_27.xlsx [options]

Options:
    --out-dir DIR      where to write resorts.json and meta.json (default: data/)
    --coords FILE      sidecar CSV with resort_name,country,latitude,longitude
                       (default: data/coordinates.csv). Used for rows whose workbook
                       has no latitude/longitude columns or leaves them blank.
    --links FILE       sidecar CSV with country,region,weather_url,avalanche_url
                       (default: data/region_links.csv). Used for rows whose workbook
                       has no weather_url/avalanche_url columns or leaves them blank.
                       A row with region "*" is the country-wide default.
    --season LABEL     season label written to meta.json (default: 2026/27)
    --sample           mark the output as sample data (shows a banner on the site)
    --check            validate only, write nothing (used by CI)

Exit codes: 0 success, 1 validation errors (listed on stderr), 2 usage or file errors.
Requires Python 3.9+ and openpyxl (pip install openpyxl).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required: pip install openpyxl")

COUNTRIES = ("FR", "IT", "AT", "CH", "DE", "SI")
TYPES = ("Glacier", "Glacier + non-glacier", "Non-glacier")
DATE_STATUSES = ("confirmed_2026_27", "estimated_from_2025_26", "year_round_glacier", "TBD")
PRICE_STATUSES = ("published_2026_27", "estimated_from_2025_26")
CURRENCIES = ("EUR", "CHF")
CONFIDENCES = ("high", "medium", "low")

# Columns that must exist in the workbook's `resorts` sheet.
REQUIRED_COLUMNS = (
    "resort_name", "local_name", "country", "region", "ski_area", "type",
    "opening_date_2026_27", "opening_date_status", "max_elevation_m", "piste_km",
    "ticket_price_min", "ticket_price_max", "currency", "price_status",
    "driving_distance_km_from_milan", "driving_time_h_from_milan", "road_head",
    "freeride_score_0_5", "ski_touring_score_0_5", "score_notes", "webcam_url",
    "comments", "sources", "confidence",
)
# Columns that may exist in the workbook; otherwise they come from the sidecar files.
OPTIONAL_COLUMNS = ("weather_url", "avalanche_url", "latitude", "longitude")

# Field order of each object in resorts.json (the data contract).
OUTPUT_FIELDS = (
    "resort_name", "local_name", "country", "region", "ski_area", "type",
    "opening_date_2026_27", "opening_date_status", "max_elevation_m", "piste_km",
    "ticket_price_min", "ticket_price_max", "currency", "price_status",
    "driving_distance_km_from_milan", "driving_time_h_from_milan", "road_head",
    "freeride_score_0_5", "ski_touring_score_0_5", "score_notes",
    "webcam_url", "weather_url", "avalanche_url", "latitude", "longitude",
    "comments", "sources", "confidence",
)

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL = re.compile(r"^https?://\S+$")


class Errors:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, where: str, msg: str) -> None:
        self.items.append(f"{where}: {msg}")

    def __bool__(self) -> bool:
        return bool(self.items)


def clean_str(v):
    """Strip strings; turn blanks into None; keep other types unchanged."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def as_int(v, where, field, err, minimum=None, maximum=None):
    if v is None:
        err.add(where, f"{field} is missing")
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        err.add(where, f"{field} must be a number, got {v!r}")
        return None
    if isinstance(v, float) and not v.is_integer():
        err.add(where, f"{field} must be a whole number, got {v!r}")
        return None
    v = int(v)
    if (minimum is not None and v < minimum) or (maximum is not None and v > maximum):
        err.add(where, f"{field}={v} outside the plausible range {minimum}..{maximum}")
    return v


def as_num(v, where, field, err, minimum=None, maximum=None, optional=False):
    if v is None:
        if not optional:
            err.add(where, f"{field} is missing")
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        err.add(where, f"{field} must be a number, got {v!r}")
        return None
    v = float(v)
    if (minimum is not None and v < minimum) or (maximum is not None and v > maximum):
        err.add(where, f"{field}={v} outside the plausible range {minimum}..{maximum}")
    return int(v) if v.is_integer() else round(v, 4)


def as_enum(v, where, field, err, allowed, optional=False):
    if v is None:
        if not optional:
            err.add(where, f"{field} is missing (allowed: {', '.join(allowed)})")
        return None
    if v not in allowed:
        err.add(where, f"{field}={v!r} is not one of {', '.join(allowed)}")
        return None
    return v


def as_url(v, where, field, err):
    if v is None:
        return None
    if not isinstance(v, str) or not URL.match(v):
        err.add(where, f"{field} must be an http(s) URL, got {v!r}")
        return None
    return v


def as_score(v, where, field, err):
    v = as_num(v, where, field, err, 0, 5)
    if v is not None and (v * 2) != int(v * 2):
        err.add(where, f"{field}={v} must be a multiple of 0.5")
    return v


def as_opening_date(v, status, where, err):
    """Excel date cell -> 'YYYY-MM-DD'; the text 'TBD' only when status is TBD."""
    if isinstance(v, dt.datetime):
        iso = v.date().isoformat()
    elif isinstance(v, dt.date):
        iso = v.isoformat()
    elif isinstance(v, str) and v.strip().upper() == "TBD":
        iso = "TBD"
    elif isinstance(v, str) and ISO_DATE.match(v.strip()):
        try:
            iso = dt.date.fromisoformat(v.strip()).isoformat()
        except ValueError:
            err.add(where, f"opening_date_2026_27={v!r} is not a valid date")
            return None
    elif v is None:
        err.add(where, "opening_date_2026_27 is missing (use a date cell or the text TBD)")
        return None
    else:
        err.add(where, f"opening_date_2026_27={v!r} is not a date cell, an ISO date string or 'TBD'")
        return None
    if status == "TBD" and iso != "TBD":
        err.add(where, f"opening_date_status is TBD but opening_date_2026_27 is {iso}")
    if status in DATE_STATUSES and status != "TBD" and iso == "TBD":
        err.add(where, f"opening_date_2026_27 is TBD but opening_date_status is {status}")
    return iso


def read_sidecar(path: Path, key_fields, err: Errors, label: str) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [k for k in key_fields if k not in (reader.fieldnames or [])]
        if missing:
            err.add(str(path), f"{label} file lacks columns {missing}")
            return {}
        return {tuple((row[k] or "").strip() for k in key_fields): row for row in reader}


def load_sheet(path: Path):
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"Cannot open workbook {path}: {exc}")
    if "resorts" not in wb.sheetnames:
        sys.exit(f"Workbook has no sheet named 'resorts' (found: {', '.join(wb.sheetnames)})")
    ws = wb["resorts"]
    rows = ws.iter_rows(values_only=True)
    header = [clean_str(h) for h in next(rows, [])]
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        sys.exit(f"Sheet 'resorts' is missing required columns: {', '.join(missing)}")
    records = []
    for i, values in enumerate(rows, start=2):
        rec = {header[j]: clean_str(values[j]) for j in range(min(len(header), len(values))) if header[j]}
        if all(v is None for v in rec.values()):
            continue  # skip fully blank trailing rows
        rec["_row"] = i
        records.append(rec)
    return header, records


def convert(args) -> tuple[list[dict], Errors]:
    err = Errors()
    header, records = load_sheet(Path(args.workbook))
    coords = read_sidecar(Path(args.coords), ("resort_name", "country"), err, "coordinates")
    links = read_sidecar(Path(args.links), ("country", "region"), err, "region links")
    has_col = {c: c in header for c in OPTIONAL_COLUMNS}

    out = []
    seen = set()
    for rec in records:
        name = rec.get("resort_name")
        where = f"row {rec['_row']} ({name or 'unnamed'})"
        if not name:
            err.add(where, "resort_name is missing")
            continue
        country = as_enum(rec.get("country"), where, "country", err, COUNTRIES)
        if (name, country) in seen:
            err.add(where, f"duplicate resort_name + country {name!r} {country}")
        seen.add((name, country))

        status = as_enum(rec.get("opening_date_status"), where, "opening_date_status", err, DATE_STATUSES)
        opening = as_opening_date(rec.get("opening_date_2026_27"), status, where, err)

        pmin = as_num(rec.get("ticket_price_min"), where, "ticket_price_min", err, 0, 400, optional=True)
        pmax = as_num(rec.get("ticket_price_max"), where, "ticket_price_max", err, 0, 400, optional=True)
        if (pmin is None) != (pmax is None):
            err.add(where, "ticket_price_min and ticket_price_max must both be set or both be blank")
        if pmin is not None and pmax is not None and pmin > pmax:
            err.add(where, f"ticket_price_min {pmin} is greater than ticket_price_max {pmax}")
        price_status = as_enum(rec.get("price_status"), where, "price_status", err, PRICE_STATUSES, optional=True)
        if pmin is not None and price_status is None:
            err.add(where, "price_status is missing although a price is given")
        currency = as_enum(rec.get("currency"), where, "currency", err, CURRENCIES)
        if country and currency and (currency == "CHF") != (country == "CH"):
            err.add(where, f"currency {currency} does not match country {country}")

        # Coordinates: workbook columns first, sidecar second.
        lat = lon = None
        if has_col["latitude"] and has_col["longitude"] and rec.get("latitude") is not None:
            lat = as_num(rec.get("latitude"), where, "latitude", err, 43, 49)
            lon = as_num(rec.get("longitude"), where, "longitude", err, 4, 18)
        else:
            side = coords.get((name, country or ""))
            if side:
                try:
                    lat = round(float(side["latitude"]), 5)
                    lon = round(float(side["longitude"]), 5)
                except (TypeError, ValueError):
                    err.add(where, f"coordinates sidecar has non-numeric values for {name}")
                else:
                    if not (43 <= lat <= 49 and 4 <= lon <= 18):
                        err.add(where, f"coordinates {lat},{lon} are outside the Alps")
            else:
                err.add(where, "no latitude/longitude in the workbook and no row in the coordinates sidecar")

        # Weather / avalanche: workbook columns first, then region links (exact region, then country default).
        region = rec.get("region")
        if not region:
            err.add(where, "region is missing")
        ski_area = rec.get("ski_area")
        if not ski_area:
            err.add(where, "ski_area is missing")
        link_row = links.get((country or "", region or "")) or links.get((country or "", "*")) or {}
        weather = as_url(rec.get("weather_url") if has_col["weather_url"] else None, where, "weather_url", err) \
            or as_url(clean_str(link_row.get("weather_url")), where, "weather_url (region_links)", err)
        avalanche = as_url(rec.get("avalanche_url") if has_col["avalanche_url"] else None, where, "avalanche_url", err) \
            or as_url(clean_str(link_row.get("avalanche_url")), where, "avalanche_url (region_links)", err)

        row = {
            "resort_name": name,
            "local_name": rec.get("local_name") if rec.get("local_name") != name else None,
            "country": country,
            "region": region,
            "ski_area": ski_area,
            "type": as_enum(rec.get("type"), where, "type", err, TYPES),
            "opening_date_2026_27": opening,
            "opening_date_status": status,
            "max_elevation_m": as_int(rec.get("max_elevation_m"), where, "max_elevation_m", err, 500, 4900),
            "piste_km": as_int(rec.get("piste_km"), where, "piste_km", err, 1, 1000),
            "ticket_price_min": pmin,
            "ticket_price_max": pmax,
            "currency": currency,
            "price_status": price_status,
            "driving_distance_km_from_milan": as_int(rec.get("driving_distance_km_from_milan"), where,
                                                     "driving_distance_km_from_milan", err, 1, 1500),
            "driving_time_h_from_milan": as_num(rec.get("driving_time_h_from_milan"), where,
                                                "driving_time_h_from_milan", err, 0.1, 15),
            "road_head": rec.get("road_head"),
            "freeride_score_0_5": as_score(rec.get("freeride_score_0_5"), where, "freeride_score_0_5", err),
            "ski_touring_score_0_5": as_score(rec.get("ski_touring_score_0_5"), where, "ski_touring_score_0_5", err),
            "score_notes": rec.get("score_notes") or "",
            "webcam_url": as_url(rec.get("webcam_url"), where, "webcam_url", err),
            "weather_url": weather,
            "avalanche_url": avalanche,
            "latitude": lat,
            "longitude": lon,
            "comments": rec.get("comments") or "",
            "sources": rec.get("sources") or "",
            "confidence": as_enum(rec.get("confidence"), where, "confidence", err, CONFIDENCES),
        }
        out.append({k: row[k] for k in OUTPUT_FIELDS})
    if not out:
        err.add("sheet resorts", "no data rows found")
    return out, err


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workbook")
    p.add_argument("--out-dir", default="data")
    p.add_argument("--coords", default="data/coordinates.csv")
    p.add_argument("--links", default="data/region_links.csv")
    p.add_argument("--season", default="2026/27")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)

    if not Path(args.workbook).exists():
        print(f"Workbook not found: {args.workbook}", file=sys.stderr)
        return 2

    rows, err = convert(args)
    if err:
        print(f"VALIDATION FAILED: {len(err.items)} problem(s) in {args.workbook}", file=sys.stderr)
        for item in err.items:
            print(f"  - {item}", file=sys.stderr)
        print("Nothing was written. Fix the cells above and run again.", file=sys.stderr)
        return 1

    n_weather = sum(1 for r in rows if r["weather_url"])
    n_aval = sum(1 for r in rows if r["avalanche_url"])
    n_cam = sum(1 for r in rows if r["webcam_url"])
    summary = (f"{len(rows)} resorts OK: {n_weather} weather links, {n_aval} avalanche links, "
               f"{n_cam} webcams, all rows have coordinates")
    if args.check:
        print(f"CHECK PASSED: {summary}")
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    body = ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows)
    (out_dir / "resorts.json").write_text("[\n" + body + "\n]\n", encoding="utf-8")
    meta = {
        "generated_at": dt.date.today().isoformat(),
        "row_count": len(rows),
        "sample": bool(args.sample),
        "season": args.season,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_dir / 'resorts.json'} and {out_dir / 'meta.json'}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
