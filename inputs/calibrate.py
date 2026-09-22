# -*- coding: utf-8 -*-
"""Print score calibration views from the enrichment files (plus overrides.csv if present):
top-25 by freeride and by ski touring, score distributions, and anchor checks.
Run from work/: PYTHONUTF8=1 python calibrate.py"""
import csv, glob, re
from collections import Counter

def num(x):
    m = re.search(r"-?\d+(\.\d+)?", str(x or ""))
    return float(m.group()) if m else None

cands = {r["id"]: r for r in csv.DictReader(open("../candidates.csv", encoding="utf-8-sig"))}
rows = {}
for p in sorted(glob.glob("enrich_*.csv")):
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if r.get("id"): rows[r["id"].strip()] = r
try:
    for o in csv.DictReader(open("overrides.csv", encoding="utf-8-sig")):
        if o["id"] in rows and o["field"] in ("freeride_score_0_5", "ski_touring_score_0_5"):
            rows[o["id"]][o["field"]] = o["value"]
except FileNotFoundError:
    pass

ANCH_FR = {"Chamonix": 5, "Verbier": 5, "Zermatt": 5, "Val d'Isère": 5, "La Grave": 5, "Engelberg": 5, "St. Anton am Arlberg": 5,
           "Tignes": 4.5, "Andermatt": 4.5, "Alagna Valsesia": 4.5, "Courmayeur": 4.5, "Lech–Zürs": 4.5, "Fieberbrunn": 4.5, "Disentis": 4.5,
           "Sölden": 4, "Saas-Fee": 4, "Davos": 4, "Les Arcs": 4, "Alpe d'Huez": 4, "Arabba–Marmolada": 4}
ANCH_ST = {"Chamonix": 5, "Zermatt": 5, "Verbier": 5, "Engelberg": 5, "Andermatt": 5, "Saas-Fee": 4.5, "Tignes": 4.5, "Val d'Isère": 4.5,
           "Courmayeur": 4.5, "Grindelwald": 4.5, "Corvatsch – Silvaplana/Sils": 4.5, "Davos": 4, "St. Moritz": 4, "Les 2 Alpes": 4, "Ischgl": 4,
           "Kühtai": 4, "Obergurgl–Hochgurgl": 3.5, "Sölden": 3.5}

def show(field, anchors, n=25):
    lst = [(num(r.get(field)), cands[i]["resort_name"], cands[i]["country"], (r.get("score_notes") or "")[:90]) for i, r in rows.items() if i in cands]
    lst = [x for x in lst if x[0] is not None]
    lst.sort(key=lambda x: (-x[0], x[1]))
    print(f"\n=== TOP {n} {field} ===")
    for s, nme, cc, note in lst[:n]: print(f"{s:>4}  {nme} ({cc}) — {note}")
    print("distribution:", sorted(Counter(x[0] for x in lst).items(), reverse=True))
    print("anchor deviations:")
    for nme, target in anchors.items():
        got = [x[0] for x in lst if x[1] == nme]
        if not got: print(f"   {nme}: MISSING"); continue
        if got[0] != target: print(f"   {nme}: got {got[0]} expected {target}")
    missing = [cands[i]["resort_name"] for i in cands if i in rows and num(rows[i].get(field)) is None]
    print("no score:", missing)

show("freeride_score_0_5", ANCH_FR)
show("ski_touring_score_0_5", ANCH_ST)
