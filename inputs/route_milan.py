# -*- coding: utf-8 -*-
"""Route every resort from Piazza del Duomo (Milan) with OSRM (public demo server, car profile),
enforcing winter pass closures: closed-pass summits are detected on the route geometry and, when all
OSRM alternatives cross a closed pass, detours are forced through via-waypoints (pass-specific detours
plus country gateway points); the fastest clean route is kept.
Usage:  PYTHONUTF8=1 python route_milan.py <input.csv> <output.csv>
input.csv columns: id, resort_name, country, base_lat, base_lon (decimal degrees)."""
import truststore; truststore.inject_into_ssl()
import requests, csv, sys, time, math

ORIGIN = (45.4642, 9.1900)  # Piazza del Duomo, Milan (lat, lon)
OSRM = "https://router.project-osrm.org/route/v1/driving/"
HD = {"User-Agent": "alpine-ski-dataset-research/1.0 (contact: giulio)"}
DEFAULT_R = 1.2  # km

# Closed passes: name -> list of (lat, lon, radius_km); ALL points must be touched for a hit
# (two-point rules distinguish a pass road from a tunnel or from a resort located at the pass).
CLOSED = {
 # brief list
 "Stelvio": [(46.5286, 10.4529, DEFAULT_R)], "Gavia": [(46.3436, 10.4903, DEFAULT_R)], "Umbrail": [(46.5397, 10.4197, DEFAULT_R)],
 "Great St Bernard pass": [(45.8692, 7.1706, 0.3)],  # tunnel alignment passes ~0.5 km east of the col
 "Furka": [(46.5722, 8.4150, DEFAULT_R)], "Grimsel": [(46.5617, 8.3381, DEFAULT_R)], "Susten": [(46.7297, 8.4469, DEFAULT_R)],
 "Nufenen": [(46.4772, 8.3872, DEFAULT_R)], "Oberalp": [(46.6592, 8.6714, DEFAULT_R)], "Klausen": [(46.8686, 8.8536, DEFAULT_R)],
 "Splügen": [(46.5054, 9.3306, DEFAULT_R)],
 "San Bernardino pass": [(46.4956, 9.1706, 0.6)],  # A13 tunnel alignment passes ~0.9 km east of the summit
 "Flüela": [(46.7500, 9.9469, DEFAULT_R)], "Albula": [(46.5831, 9.8367, DEFAULT_R)], "Galibier": [(45.0642, 6.4078, DEFAULT_R)],
 "Iseran": [(45.4172, 7.0308, DEFAULT_R)], "Petit Saint-Bernard": [(45.6800, 6.8836, DEFAULT_R)], "Bonette": [(44.3231, 6.8069, DEFAULT_R)],
 "Cayolle": [(44.2597, 6.7431, DEFAULT_R)], "Agnel": [(44.6844, 6.9797, DEFAULT_R)], "Lombarde": [(44.2011, 7.1447, 0.8)],
 "Timmelsjoch": [(46.9067, 11.0961, DEFAULT_R)], "Silvretta Bielerhöhe": [(46.9178, 10.0958, DEFAULT_R)],
 "Grossglockner Hochtor": [(47.0817, 12.8422, DEFAULT_R)], "Grossglockner Fuscher Törl": [(47.1333, 12.8250, DEFAULT_R)],
 # standard winter closures not listed in the brief
 "Gotthard pass": [(46.5590, 8.5614, DEFAULT_R)], "Lukmanier": [(46.5636, 8.8003, DEFAULT_R)], "Forcola di Livigno": [(46.4342, 10.0648, DEFAULT_R)],
 "Izoard": [(44.8203, 6.7350, DEFAULT_R)], "Mont Cenis": [(45.2597, 6.9008, DEFAULT_R)], "Colombière": [(45.9928, 6.4736, DEFAULT_R)],
 "Joux Plane": [(46.1436, 6.7106, DEFAULT_R)], "Croix de Fer": [(45.2272, 6.1917, DEFAULT_R)], "Glandon": [(45.2389, 6.1739, DEFAULT_R)],
 "Madeleine": [(45.4300, 6.3736, 0.8)], "Cormet de Roselend": [(45.6811, 6.7014, DEFAULT_R)], "Sarenne": [(45.0839, 6.1339, DEFAULT_R)],
 "Allos": [(44.2986, 6.5947, 1.0), (44.3406, 6.6217, 1.5)],  # col + northern ramp (La Foux d'Allos village is near the col)
 "Champs": [(44.1897, 6.6764, DEFAULT_R)], "Couillole": [(44.1067, 7.0089, DEFAULT_R)], "Noyer": [(44.6858, 5.9764, DEFAULT_R)],
 "Penser Joch": [(46.8153, 11.4432, DEFAULT_R)], "Fedaia": [(46.4589, 11.8622, DEFAULT_R)], "Manghen": [(46.1739, 11.4353, DEFAULT_R)],
 "Finestre": [(45.0722, 7.0558, DEFAULT_R)], "San Carlo": [(45.6919, 6.9797, DEFAULT_R)], "Pfitscher Joch": [(46.9908, 11.6606, DEFAULT_R)],
 "Staller Sattel": [(46.8925, 12.2050, DEFAULT_R)],
 "Pramollo/Nassfeld pass (Italian ramp)": [(46.5580, 13.2796, 1.5), (46.5461, 13.2988, 0.5)],  # pass + point on the SR110 ramp above Pontebba
 "Sölk": [(47.2778, 13.9186, DEFAULT_R)], "Col de la Croix": [(46.3247, 7.0844, DEFAULT_R)], "Sanetsch": [(46.3608, 7.2989, DEFAULT_R)],
 "Bassachaux": [(46.2556, 6.7717, DEFAULT_R)],
 "Joux Verte": [(46.1972, 6.7622, 0.6), (46.2080, 6.7400, 1.0)],  # col + Lac de Montriond (Avoriaz sits by the col)
 "Passo delle Erbe": [(46.7339, 11.8153, DEFAULT_R)], "Duran": [(46.3364, 12.0972, DEFAULT_R)], "Hahntennjoch": [(47.2947, 10.6797, DEFAULT_R)],
 "Pragel": [(47.0206, 8.8542, DEFAULT_R)], "Glaubenbielen": [(46.8264, 8.1189, DEFAULT_R)],
 "Glaubenberg": [(46.8869, 8.1786, DEFAULT_R)], "Lech–Warth road (Tannberg)": [(47.2290, 10.1630, DEFAULT_R)],
}
VIA = {
 "Merano": (46.6680, 11.1600), "Bormio": (46.4676, 10.3708), "Brig": (46.3167, 7.9878), "Göschenen": (46.6667, 8.5900),
 "Mesocco": (46.3937, 9.2333), "Bivio": (46.4686, 9.6503), "Klosters": (46.8690, 9.8790), "Filisur": (46.6750, 9.6850),
 "Modane": (45.2000, 6.6700), "Bourg-d'Oisans": (45.0550, 6.0300), "Bourg-Saint-Maurice": (45.6186, 6.7694),
 "Chamonix": (45.9237, 6.8694), "Nice": (43.7102, 7.2620), "Digne": (44.0925, 6.2356), "Briançon": (44.8992, 6.6425),
 "Ötztal Bahnhof": (47.2333, 10.8583), "Bludenz": (47.1543, 9.8219), "Landeck": (47.1400, 10.5700),
 "Matrei in Osttirol": (47.0000, 12.5350), "Spittal": (46.7917, 13.4958), "Bressanone": (46.7150, 11.6560),
 "Passo Pordoi": (46.4878, 11.8127), "Caprile": (46.4364, 11.9925), "Steeg": (47.2411, 10.2973), "Schoppernau": (47.3131, 10.0186),
 "Arnoldstein": (46.5480, 13.7110), "Cluses": (46.0600, 6.5800), "Taninges": (46.1078, 6.5920), "Morzine": (46.1792, 6.7089),
 "Saint-Jean-de-Maurienne": (45.2764, 6.3467), "Moûtiers": (45.4853, 6.5333), "Albertville": (45.6755, 6.3928),
 "Gap": (44.5594, 6.0786), "Aigle": (46.3180, 6.9700), "Oulx": (45.0330, 6.8320), "Pré-Saint-Didier": (45.7642, 6.9861),
 "Innsbruck": (47.2692, 11.4041), "Lienz": (46.8300, 12.7690), "Radstadt": (47.3833, 13.4500), "Imst": (47.2400, 10.7400),
 "Brunico": (46.7970, 11.9360), "Agordo": (46.2820, 12.0330), "Lucerne": (47.0502, 8.3093), "Trento": (46.0700, 11.1200),
 "Schwyz": (47.0208, 8.6541), "Barcelonnette": (44.3870, 6.6520), "Sion": (46.2276, 7.3589), "Aosta": (45.7370, 7.3200),
 "Chur": (46.8499, 9.5329), "Zernez": (46.6990, 10.0920), "Tirano": (46.2160, 10.1690), "Chiavenna": (46.3210, 9.3990),
 "Colmars": (44.1811, 6.6264), "Cuneo": (44.3845, 7.5427), "Tröpolach": (46.6090, 13.2830), "Villach": (46.6111, 13.8558),
 "Ilanz": (46.7747, 9.2050),
}
DETOUR = {
 "Stelvio": ["Merano"], "Umbrail": ["Merano", "Bormio"], "Gavia": ["Bormio", "Trento"],
 "Great St Bernard pass": ["Aosta", "Brig"], "Furka": ["Göschenen", "Brig"], "Grimsel": ["Göschenen", "Brig"],
 "Susten": ["Göschenen", "Lucerne"], "Nufenen": ["Göschenen", "Brig"], "Gotthard pass": ["Göschenen", "Brig"],
 "Oberalp": ["Chur", "Göschenen", "Mesocco"], "Lukmanier": ["Chur", "Mesocco", "Bivio"], "Klausen": ["Schwyz", "Chur"],
 "Splügen": ["Mesocco", "Bivio"], "San Bernardino pass": ["Mesocco", "Bivio"], "Flüela": ["Klosters", "Filisur", "Zernez"],
 "Albula": ["Bivio", "Filisur"], "Forcola di Livigno": ["Bormio", "Zernez"], "Galibier": ["Modane", "Bourg-d'Oisans"],
 "Iseran": ["Bourg-Saint-Maurice", "Modane"], "Petit Saint-Bernard": ["Chamonix", "Modane"], "Mont Cenis": ["Modane", "Oulx"],
 "Bonette": ["Nice", "Barcelonnette"], "Cayolle": ["Nice", "Digne"], "Allos": ["Colmars", "Digne", "Nice"], "Champs": ["Digne", "Nice"],
 "Lombarde": ["Nice"], "Couillole": ["Nice"], "Agnel": ["Briançon"], "Izoard": ["Briançon"], "Noyer": ["Gap"],
 "Timmelsjoch": ["Ötztal Bahnhof", "Innsbruck"], "Silvretta Bielerhöhe": ["Bludenz", "Landeck"],
 "Grossglockner Hochtor": ["Matrei in Osttirol", "Spittal"], "Grossglockner Fuscher Törl": ["Matrei in Osttirol", "Spittal"],
 "Penser Joch": ["Bressanone"], "Fedaia": ["Passo Pordoi", "Caprile"], "Manghen": ["Trento"], "Finestre": ["Oulx"],
 "San Carlo": ["Pré-Saint-Didier"], "Pfitscher Joch": ["Innsbruck"], "Staller Sattel": ["Lienz"],
 "Pramollo/Nassfeld pass (Italian ramp)": ["Tröpolach"], "Sölk": ["Radstadt"], "Col de la Croix": ["Aigle"], "Sanetsch": ["Sion"],
 "Colombière": ["Cluses", "Albertville"], "Joux Plane": ["Cluses", "Taninges"], "Bassachaux": ["Morzine", "Cluses"], "Joux Verte": ["Morzine"],
 "Croix de Fer": ["Saint-Jean-de-Maurienne"], "Glandon": ["Saint-Jean-de-Maurienne"], "Madeleine": ["Moûtiers", "Saint-Jean-de-Maurienne"],
 "Cormet de Roselend": ["Albertville"], "Sarenne": ["Bourg-d'Oisans"], "Passo delle Erbe": ["Brunico"], "Duran": ["Agordo"],
 "Hahntennjoch": ["Imst"], "Pragel": ["Schwyz"], "Glaubenbielen": ["Lucerne"], "Glaubenberg": ["Lucerne"],
 "Lech–Warth road (Tannberg)": ["Steeg", "Schoppernau"],
}
GATEWAYS = {
 "CH": ["Brig", "Aosta", "Göschenen", "Mesocco", "Chur", "Bivio", "Chiavenna", "Tirano", "Zernez", "Merano"],
 "FR": ["Chamonix", "Modane", "Oulx", "Nice", "Barcelonnette", "Briançon", "Bourg-d'Oisans", "Albertville", "Cluses", "Cuneo"],
 "AT": ["Innsbruck", "Merano", "Lienz", "Spittal", "Villach", "Bludenz", "Landeck", "Ötztal Bahnhof"],
 "DE": ["Innsbruck", "Merano", "Bludenz", "Imst"],
 "IT": ["Merano", "Bormio", "Trento", "Aosta", "Oulx", "Chiavenna", "Tirano", "Brunico"],
}

def hav(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(d))

LOG = []
def osrm(points, alternatives=True):
    coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in points)
    url = OSRM + coords + "?overview=full&geometries=geojson&steps=true" + ("&alternatives=3" if alternatives else "")
    for attempt in range(5):
        try:
            r = requests.get(url, headers=HD, timeout=60)
            if r.status_code == 200:
                j = r.json()
                if j.get("code") == "Ok":
                    snap = j["waypoints"][-1].get("distance", 0)
                    for rt in j["routes"]:
                        rt["_snap_m"] = snap
                    return j["routes"]
                LOG.append(("osrm_code", j.get("code"), url[:120])); return []
            LOG.append(("http", r.status_code, url[:120]))
            time.sleep(4 + 4 * attempt)
        except Exception as e:
            LOG.append(("exc", repr(e)[:80], url[:120])); time.sleep(4 + 4 * attempt)
    return []

def touches(geom, lat, lon, r):
    for glon, glat in geom:
        if abs(glat - lat) < 0.03 and abs(glon - lon) < 0.045 and hav((glat, glon), (lat, lon)) <= r:
            return True
    return False

IGNORE = set()  # per-row pass names to ignore (input column ignore_passes, ';'-separated)
def hits(route, dest):
    geom = route["geometry"]["coordinates"]
    found = set()
    for name, pts in CLOSED.items():
        if name in IGNORE:
            continue
        # destination-at-pass exemption for single-point rules (e.g. Passo dello Stelvio summer ski area)
        if len(pts) == 1 and hav(dest, (pts[0][0], pts[0][1])) <= 1.0:
            continue
        if all(touches(geom, lat, lon, r) for lat, lon, r in pts):
            found.add(name)
    # NOTE: no road-name check — access roads are often named after the pass they lead to
    # (e.g. "Route du Col de la Croix de Fer" through Saint-Sorlin, SS38 "dello Stelvio" in Bormio).
    return found

NAME_KEYWORDS = {
 "Lombarde": ["col de la lombarde", "colle della lombarda"], "Stelvio": ["passo dello stelvio", "stilfser joch", "stilfserjoch"],
 "Gavia": ["passo di gavia", "passo gavia"], "Umbrail": ["umbrail"], "Galibier": ["col du galibier"], "Iseran": ["col de l'iseran"],
 "Bonette": ["col de la bonette", "cime de la bonette", "restefond"], "Cayolle": ["col de la cayolle"], "Agnel": ["col agnel", "colle dell'agnello"],
 "Izoard": ["col d'izoard"], "Mont Cenis": ["col du mont-cenis", "col du mont cenis", "colle del moncenisio"], "Albula": ["albulapass"],
 "Klausen": ["klausenpass"], "Splügen": ["splügenpass", "passo dello spluga"], "Nufenen": ["nufenenpass", "passo della novena"],
 "Grimsel": ["grimselpass"], "Lukmanier": ["lukmanierpass", "passo del lucomagno"], "Forcola di Livigno": ["forcola di livigno"],
 "Fedaia": ["passo fedaia"], "Penser Joch": ["penser joch", "passo di pennes", "penserjoch"], "Staller Sattel": ["staller sattel", "passo stalle"],
 "Colombière": ["col de la colombière"], "Joux Plane": ["col de joux plane"], "Croix de Fer": ["col de la croix de fer"],
 "Glandon": ["col du glandon"], "Cormet de Roselend": ["cormet de roselend"], "Sarenne": ["col de sarenne"], "Champs": ["col des champs"],
 "Couillole": ["col de la couillole"], "Noyer": ["col du noyer"], "Finestre": ["colle delle finestre"], "Manghen": ["passo manghen"],
}

def non_driving_modes(route):
    modes = set()
    for leg in route["legs"]:
        for st in leg["steps"]:
            m = st.get("mode", "driving")
            if m != "driving":
                modes.add(m)
    return modes

def pack(r, via, primary_hits, status):
    return dict(distance_km=r["distance"] / 1000, hours=r["duration"] / 3600, via=via, hits_primary=";".join(sorted(primary_hits)),
                modes=";".join(sorted(non_driving_modes(r))), status=status, snap_m=round(r.get("_snap_m", 0)))

def route_one(dest, country, force_via=""):
    if force_via:
        vias = [v.strip() for v in force_via.split("+") if v.strip()]
        time.sleep(1.05)
        rs = osrm([ORIGIN] + [VIA[v] for v in vias] + [dest], alternatives=False)
        if rs:
            h = hits(rs[0], dest)
            return pack(rs[0], force_via, h, "forced_via" if not h else "UNRESOLVED closed pass: " + ";".join(sorted(h)))
        return dict(status="no_route")
    time.sleep(1.05)
    routes = osrm([ORIGIN, dest])
    if not routes:
        return dict(status="no_route")
    primary_hits = hits(routes[0], dest)
    clean = [r for r in routes if not hits(r, dest)]
    if clean:
        best = min(clean, key=lambda r: r["duration"])
        return pack(best, "", primary_hits, "ok" if not primary_hits else "alternative_used")
    vias = []
    for p in sorted(primary_hits):
        for v in DETOUR.get(p, []):
            if v not in vias: vias.append(v)
    for v in GATEWAYS.get(country, []):
        if v not in vias: vias.append(v)
    tried = []
    for v in vias:
        time.sleep(1.05)
        for r in osrm([ORIGIN, VIA[v], dest], alternatives=False):
            tried.append((r["duration"], v, hits(r, dest), r))
    ok = [t for t in tried if not t[2]]
    if ok:
        dur, v, _, r = min(ok, key=lambda t: t[0])
        return pack(r, v, primary_hits, "detour_forced")
    for dur, v, h, r in sorted(tried, key=lambda t: t[0])[:4]:
        for p in sorted(h):
            for v2 in DETOUR.get(p, []):
                if v2 == v: continue
                time.sleep(1.05)
                for r2 in osrm([ORIGIN, VIA[v], VIA[v2], dest], alternatives=False):
                    if not hits(r2, dest):
                        return pack(r2, f"{v}+{v2}", primary_hits, "detour_forced_2")
    return pack(routes[0], "", primary_hits, "UNRESOLVED closed pass: " + ";".join(sorted(primary_hits)))

if __name__ == "__main__":
    inp, outp = sys.argv[1], sys.argv[2]
    rows = list(csv.DictReader(open(inp, encoding="utf-8")))
    done = {}
    try:
        for r in csv.DictReader(open(outp, encoding="utf-8")):
            done[r["id"]] = r
    except FileNotFoundError:
        pass
    fields = ["id", "resort_name", "country", "base_lat", "base_lon", "distance_km", "hours", "via", "hits_primary", "modes", "status", "snap_m"]
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            d = done.get(r["id"])
            if d and d.get("status", "").startswith(("ok", "alternative", "detour", "forced")) and d.get("base_lat") == r["base_lat"] and d.get("base_lon") == r["base_lon"]:
                w.writerow(d); f.flush(); continue
            try:
                dest = (float(r["base_lat"]), float(r["base_lon"]))
            except Exception:
                w.writerow(dict(id=r["id"], resort_name=r["resort_name"], country=r["country"], status="no_coords")); f.flush(); continue
            IGNORE = set(x.strip() for x in (r.get("ignore_passes") or "").split(";") if x.strip())
            res = route_one(dest, r["country"], (r.get("force_via") or "").strip())
            out = dict(id=r["id"], resort_name=r["resort_name"], country=r["country"], base_lat=r["base_lat"], base_lon=r["base_lon"])
            for k, v in res.items():
                out[k] = f"{v:.1f}" if k == "distance_km" else f"{v:.3f}" if k == "hours" else v
            w.writerow(out); f.flush()
            print(out["id"], out["resort_name"], out.get("distance_km"), out.get("hours"), out.get("status"), out.get("via"), "snap", out.get("snap_m"), flush=True)
    if LOG:
        print("LOG entries:", len(LOG)); print(LOG[:10])
