# -*- coding: utf-8 -*-
"""Rebuild routes.csv from the router logs (single-writer records), keeping only clean 'ok' rows as cache.
Coordinates are taken from routes_in.csv (must match what the router used). Everything else is recomputed
by route_milan.py on the next run. Usage: PYTHONUTF8=1 python rebuild_routes.py"""
import csv, re, glob

pat = re.compile(r"^(\d+) (.+?) (\d+\.\d) (\d+\.\d{3}) (ok|alternative_used|detour_forced(?:_2)?|forced_via|UNRESOLVED[^\n]*?) ?(\S*) snap (\d+)$")
coords = {r["id"]: r for r in csv.DictReader(open("routes_in.csv", encoding="utf-8"))}
best = {}
for lg in sorted(glob.glob("route_log_*.txt")):
    for line in open(lg, encoding="utf-8", errors="replace"):
        m = pat.match(line.strip())
        if not m: continue
        rid, name, dist, hours, status, via, snap = m.groups()
        if status != "ok": continue
        if rid in coords:
            best[rid] = dict(id=rid, resort_name=coords[rid]["resort_name"], country=coords[rid]["country"], base_lat=coords[rid]["base_lat"],
                             base_lon=coords[rid]["base_lon"], distance_km=dist, hours=hours, via="", hits_primary="", modes="", status="ok", snap_m=snap)
fields = ["id", "resort_name", "country", "base_lat", "base_lon", "distance_km", "hours", "via", "hits_primary", "modes", "status", "snap_m"]
with open("routes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for rid in sorted(best, key=int): w.writerow(best[rid])
print("clean ok rows cached:", len(best), "of", len(coords), "in routes_in.csv")
