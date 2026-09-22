# -*- coding: utf-8 -*-
"""Build routes_in.csv for route_milan.py from the enrichment files.
Uses agent-supplied base_lat/base_lon; falls back to Nominatim (OpenStreetMap) geocoding of the road head or resort
name when missing or implausible, and flags the source. Run from work/: PYTHONUTF8=1 python geocode_fallback.py"""
import truststore; truststore.inject_into_ssl()
import csv, glob, time, re, sys, requests

HD = {"User-Agent": "alpine-ski-dataset-research/1.0 (contact: giulio.carassai@oliverwyman.com)"}
BBOX = {"FR": (43.5, 47.0, 5.0, 7.8), "IT": (44.0, 47.2, 6.6, 13.9), "AT": (46.3, 48.2, 9.5, 15.2), "CH": (45.8, 47.9, 5.9, 10.6), "DE": (47.2, 48.0, 9.8, 13.2)}
CC = {"FR": "fr", "IT": "it", "AT": "at", "CH": "ch", "DE": "de"}
SPECIAL_VIA = {"Nassfeld": ""}  # add force_via per resort if needed
IGNORE = {"Passo dello Stelvio": "Umbrail;Stelvio"}
# coordinator coordinate fixes (id -> lat, lon): agent point was not the valley/base station
COORD_OVERRIDES = {"169": (46.9618, 13.0572)}  # Mölltal Glacier: Innerfragant valley station area (agent point was the upper station)

def num(x):
    m = re.search(r"-?\d+(\.\d+)?", str(x or "").replace(",", "."))
    return float(m.group()) if m else None

def plausible(cc, lat, lon):
    b = BBOX.get(cc)
    return b and b[0] <= lat <= b[1] and b[2] <= lon <= b[3]

def geocode(q, cc):
    time.sleep(1.1)
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", params=dict(q=q, format="json", limit=1, countrycodes=CC[cc]), headers=HD, timeout=30)
        j = r.json()
        if j: return float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("display_name", "")[:80]
    except Exception as e:
        return None
    return None

cands = {r["id"]: r for r in csv.DictReader(open("../candidates.csv", encoding="utf-8-sig"))}
enr = {}
for p in sorted(glob.glob("enrich_*.csv")):
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if r.get("id"): enr[r["id"].strip()] = r
out = []
for cid, c in cands.items():
    e = enr.get(cid, {})
    if (e.get("comments") or "").strip().upper().startswith("EXCLUDE"): continue
    lat, lon = num(e.get("base_lat")), num(e.get("base_lon"))
    src = "agent"
    if cid in COORD_OVERRIDES:
        lat, lon = COORD_OVERRIDES[cid]; src = "coordinator"
    if "--no-geocode" in sys.argv and (lat is None or lon is None or not plausible(c["country"], lat, lon)):
        continue  # partial run: only rows with agent coordinates
    if lat is None or lon is None or not plausible(c["country"], lat, lon):
        q = (e.get("road_head") or "").strip() or c.get("road_head_hint", "").split("(")[0].strip() or c["resort_name"]
        g = geocode(q, c["country"])
        if g and plausible(c["country"], g[0], g[1]):
            lat, lon, src = g[0], g[1], f"nominatim:{q}"
        else:
            g = geocode(c["resort_name"], c["country"])
            if g and plausible(c["country"], g[0], g[1]): lat, lon, src = g[0], g[1], f"nominatim:{c['resort_name']}"
            else: lat, lon, src = None, None, "MISSING"
    out.append(dict(id=cid, resort_name=c["resort_name"], country=c["country"], base_lat=f"{lat:.5f}" if lat else "", base_lon=f"{lon:.5f}" if lon else "",
                    ignore_passes=IGNORE.get(c["resort_name"], ""), force_via=SPECIAL_VIA.get(c["resort_name"], ""), coord_source=src))
    if src != "agent": print(cid, c["resort_name"], src, lat, lon)
with open("routes_in.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("rows:", len(out), "| agent coords:", sum(1 for o in out if o["coord_source"] == "agent"), "| geocoded:", sum(1 for o in out if o["coord_source"].startswith("nominatim")), "| missing:", sum(1 for o in out if o["coord_source"] == "MISSING"))
