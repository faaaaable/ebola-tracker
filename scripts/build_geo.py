#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare la géométrie des zones de santé, une fois pour toutes.

Le fond de carte ne change jamais ; seuls les chiffres changent chaque jour.
Ce script est donc distinct de scripts/build_pages.py : il se lance à la
demande, pas à chaque génération du site, et produit deux fichiers que le
reste de la chaîne consomme sans jamais retélécharger les 6,2 Mo de source.

    site/geo/zones-overview.json   tracés SVG très simplifiés des 519 zones,
                                   pour la carte d'aperçu écrite en dur dans
                                   la page d'accueil
    data/health-zones.geojson      polygones des zones des provinces touchées,
                                   au détail utile pour la carte Leaflet

Source : shapefile officiel des 519 zones de santé de la RDC, publié par
OCHA sur HDX (jeu de données « dr-congo-health-0 »). On passe par l'API CKAN
plutôt que par un lien deviné : la page web bloque les requêtes automatisées,
l'API est prévue pour ça.

Dépendance : pyshp uniquement (`pip install pyshp`) — un paquet Python pur.
geopandas ferait le même travail mais impose GDAL, inutile ici.

Usage :  python scripts/build_geo.py [--force]
"""

import io
import json
import os
import sys
import unicodedata
import urllib.request
import zipfile

try:
    import shapefile  # pyshp
except ImportError:
    sys.exit("pyshp est requis : pip install pyshp")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "geo")
HDX_API = "https://data.humdata.org/api/3/action/package_show?id=dr-congo-health-0"
RESOURCE = "RDC_Zone_de_sante_09092019.zip"
UA = {"User-Agent": "ebola-tracker.org build_geo"}

# Tolérances de simplification, en degrés (1° ≈ 111 km à l'équateur).
# La carte d'aperçu ne fait que quelques centaines de pixels de large : le
# reste du pays n'y sert que de contexte et peut être très simplifié. Les zones
# touchées, en revanche, sont celles qu'on regarde — on les garde plus fines.
TOL_OVERVIEW = 0.08          # ~9 km, pour les zones sans cas
TOL_OVERVIEW_AFFECTED = 0.02  # ~2 km, pour les zones touchées
TOL_DETAIL = 0.005     # ~500 m : reserve au GeoJSON

# Cartes de province : on y regarde une province a la loupe, il faut donc un
# trace plus fin que sur la carte du pays. Les zones voisines n'y servent que
# de contexte et restent grossieres.
TOL_PROVINCE = 0.009        # ~1 km, pour les zones de la province
TOL_PROVINCE_AROUND = 0.05  # ~5 km : les voisines ne sont qu une silhouette
PROVINCE_MARGIN = 0.14      # marge autour de la province, en part de sa taille
DECIMALS_OVERVIEW = 1  # coordonnées déjà projetées en pixels
DECIMALS_DETAIL = 4    # ~11 m, largement suffisant après simplification
OVERVIEW_WIDTH = 1000.0

sys.setrecursionlimit(20000)


# --------------------------------------------------------------------------
# Récupération de la source
# --------------------------------------------------------------------------

def fetch(url, path, force=False):
    if os.path.exists(path) and os.path.getsize(path) > 1000 and not force:
        print("  en cache : %s" % os.path.basename(path))
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print("  téléchargement : %s" % os.path.basename(path))
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=300) as resp, io.open(path, "wb") as out:
        out.write(resp.read())
    return path


def load_shapefile(force=False):
    api = fetch(HDX_API, os.path.join(CACHE, "hdx.json"), force)
    resources = json.load(io.open(api, encoding="utf-8"))["result"]["resources"]
    url = next((r["url"] for r in resources if r.get("name") == RESOURCE), None)
    if not url:
        url = next(r["url"] for r in resources
                   if str(r.get("format", "")).upper() == "SHP")
    archive = fetch(url, os.path.join(CACHE, RESOURCE), force)

    folder = os.path.join(CACHE, "shp")
    if not os.path.isdir(folder) or force:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(folder)
    for base, _dirs, files in os.walk(folder):
        for name in files:
            if name.lower().endswith(".shp"):
                return os.path.join(base, name)
    sys.exit("aucun .shp trouvé dans l'archive")


# --------------------------------------------------------------------------
# Rapprochement des noms
#
# Le shapefile et nos bulletins n'écrivent pas les noms de la même façon :
# « Mongbwalu » contre « Mongbalu », « Wanie-Rukula » contre « Wanierukula ».
# On rapproche en trois passes, de la plus stricte à la plus tolérante, et on
# refuse tout ce qui reste ambigu plutôt que de deviner.
# --------------------------------------------------------------------------

def normalise(text, tight=False):
    text = unicodedata.normalize("NFD", str(text or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    for char in "-_'’.":
        text = text.replace(char, " ")
    text = " ".join(text.lower().split())
    return text.replace(" ", "") if tight else text


def edit_distance(a, b):
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        current = [i + 1]
        for j, cb in enumerate(b):
            current.append(min(previous[j + 1] + 1, current[j] + 1,
                               previous[j] + (ca != cb)))
        previous = current
    return previous[-1]


def match_zones(records, our_zones):
    """Associe chaque zone de nos données à sa clé dans le shapefile."""
    index = {}
    for rec, _shape in records:
        index.setdefault(normalise(rec["Nom"], True), []).append(rec)

    mapping, report, aliases = {}, [], {}
    for zone in our_zones:
        name, province = zone["name"], zone.get("province")
        key = normalise(name, True)
        if key in index:
            mapping[key] = zone
            report.append((name, index[key][0]["Nom"], "exact"))
            continue
        pool = [r for r, _ in records if normalise(r["PROVINCE"]) == normalise(province)]
        best = min(pool, key=lambda r: edit_distance(normalise(name), normalise(r["Nom"])),
                   default=None)
        gap = edit_distance(normalise(name), normalise(best["Nom"])) if best else 99
        if best and gap <= 2:
            mapping[normalise(best["Nom"], True)] = zone
            aliases[key] = normalise(best["Nom"], True)
            report.append((name, best["Nom"], "orthographe (%d)" % gap))
        else:
            report.append((name, best["Nom"] if best else "—", "NON TROUVÉE"))
    return mapping, report, aliases


# --------------------------------------------------------------------------
# Géométrie
# --------------------------------------------------------------------------

def simplify(points, tolerance):
    """Douglas-Peucker. Écarte les sommets qui s'éloignent de moins de
    `tolerance` de la corde — le détail invisible à l'écran visé."""
    if len(points) < 3:
        return points
    first, last = points[0], points[-1]
    dx, dy = last[0] - first[0], last[1] - first[1]
    span = (dx * dx + dy * dy) ** 0.5
    index, farthest = 0, 0.0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if span == 0:
            distance = ((px - first[0]) ** 2 + (py - first[1]) ** 2) ** 0.5
        else:
            distance = abs(dy * px - dx * py + last[0] * first[1]
                           - last[1] * first[0]) / span
        if distance > farthest:
            index, farthest = i, distance
    if farthest <= tolerance:
        return [first, last]
    return (simplify(points[:index + 1], tolerance)[:-1]
            + simplify(points[index:], tolerance))


def rings(shape):
    parts = list(shape.parts) + [len(shape.points)]
    return [shape.points[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]


def simplify_safely(ring, tolerance):
    """Simplifie sans jamais faire disparaître une zone.

    Une zone urbaine — Goma, Bunia, les zones de Kinshasa — est plus petite
    que la tolérance visée : simplifiée telle quelle, son contour se réduit à
    deux points et elle s'efface de la carte. On redescend alors par paliers
    jusqu'à obtenir une forme valide, quitte à ne pas simplifier du tout : ces
    zones ont peu de sommets, le coût est négligeable.
    """
    for level in (tolerance, tolerance / 4.0, tolerance / 16.0, 0):
        simple = simplify(ring, level) if level else list(ring)
        if len(simple) >= 4:
            return simple
    return None


# --------------------------------------------------------------------------

def affected_provinces_names(config, latest):
    """Noms des provinces touchees, tels qu'ecrits dans nos donnees."""
    known = set(config.get("provinceSlugs", {}))
    return [p["name"] for p in latest.get("provinces", []) if p["name"] in known]


def main():
    force = "--force" in sys.argv
    print("1. Source")
    shp = load_shapefile(force)
    reader = shapefile.Reader(shp, encoding="utf-8", encodingErrors="replace")
    fields = [f[0] for f in reader.fields[1:]]
    records = [(dict(zip(fields, sr.record)), sr.shape) for sr in reader.iterShapeRecords()]
    print("  %d zones de santé lues" % len(records))

    latest = json.load(io.open(os.path.join(ROOT, "data", "latest.json"), encoding="utf-8"))
    our_zones = latest.get("healthZones", [])
    affected_provinces = {normalise(p["name"]) for p in latest.get("provinces", [])}

    print("\n2. Rapprochement des noms")
    mapping, report, aliases = match_zones(records, our_zones)
    missing = [r for r in report if r[2] == "NON TROUVÉE"]
    for name, found, how in report:
        if how != "exact":
            print("  %-22s -> %-22s %s" % (name, found, how))
    print("  %d/%d zones rapprochées" % (len(report) - len(missing), len(report)))
    if missing:
        print("  ! zones sans polygone :", ", ".join(m[0] for m in missing))

    print("\n3. Aperçu SVG des 519 zones")
    xs = [p[0] for _, s in records for p in s.points]
    ys = [p[1] for _, s in records for p in s.points]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    # Les repères géographiques peuvent tomber hors du pays — Kampala est en
    # Ouganda. On élargit l'emprise pour qu'ils tiennent dans le cadre, plutôt
    # que de les rogner.
    config = json.load(io.open(os.path.join(ROOT, "site", "pages.json"), encoding="utf-8"))
    places = config.get("mapLandmarks", {}).get("places", [])
    for place in places:
        minx, maxx = min(minx, place["lon"] - 0.4), max(maxx, place["lon"] + 0.4)
        miny, maxy = min(miny, place["lat"] - 0.4), max(maxy, place["lat"] + 0.4)

    scale = OVERVIEW_WIDTH / (maxx - minx)
    height = round((maxy - miny) * scale, 1)

    def project(lon, lat):
        """Coordonnées géographiques -> repère du viewBox SVG."""
        return round((lon - minx) * scale, 1), round((maxy - lat) * scale, 1)

    zones = []
    for rec, shape in records:
        key = normalise(rec["Nom"], True)
        tolerance = TOL_OVERVIEW_AFFECTED if key in mapping else TOL_OVERVIEW
        subpaths = []
        for ring in rings(shape):
            simple = simplify_safely(ring, tolerance)
            if simple is None:
                continue
            pts = ["%.*f %.*f" % (DECIMALS_OVERVIEW, (x - minx) * scale,
                                  DECIMALS_OVERVIEW, (maxy - y) * scale)
                   for x, y in simple]
            subpaths.append("M" + "L".join(pts) + "Z")
        if not subpaths:
            continue
        px = [(x - minx) * scale for x, _ in shape.points]
        py = [(maxy - y) * scale for _, y in shape.points]
        zones.append({"name": rec["Nom"], "province": rec["PROVINCE"],
                      "key": key, "d": "".join(subpaths),
                      # Emprise dans le repère du viewBox : le zoom au clic
                      # n'a ainsi aucun calcul géométrique à refaire.
                      "box": [round(min(px), 1), round(min(py), 1),
                              round(max(px) - min(px), 1), round(max(py) - min(py), 1)]})

    province_boxes = {}
    for zone in zones:
        x, y, w, h = zone["box"]
        current = province_boxes.get(zone["province"])
        if current is None:
            province_boxes[zone["province"]] = [x, y, x + w, y + h]
        else:
            current[0] = min(current[0], x)
            current[1] = min(current[1], y)
            current[2] = max(current[2], x + w)
            current[3] = max(current[3], y + h)
    province_boxes = {name: [round(b[0], 1), round(b[1], 1),
                             round(b[2] - b[0], 1), round(b[3] - b[1], 1)]
                      for name, b in province_boxes.items()}

    # Goma et Bukavu sont marquees "overview": false : a l'echelle du pays,
    # elles nomment des zones grises a 500 km du foyer, ce qui laisse croire
    # qu'il s'y passe quelque chose. Elles restent sur la carte de leur
    # province, ou elles servent vraiment de point de repere.
    landmarks = []
    for place in places:
        if place.get("overview") is False:
            continue
        x, y = project(place["lon"], place["lat"])
        landmarks.append({"name": place["name"], "kind": place["kind"],
                          "province": place.get("province"), "x": x, "y": y})

    overview = {
        "_comment": ("Tracés SVG des 519 zones de santé, simplifiés à ~3 km et "
                     "projetés dans un viewBox. Produit par scripts/build_geo.py "
                     "depuis le shapefile HDX/OCHA. Ne pas modifier à la main."),
        "viewBox": "0 0 %d %s" % (OVERVIEW_WIDTH, height),
        "source": "HDX/OCHA — dr-congo-health-0",
        # Ecarts d'orthographe entre nos bulletins et le shapefile, resolus ici
        # une fois pour toutes : la generation quotidienne des pages n'a plus
        # qu'a consulter cette table, sans refaire de rapprochement approche.
        "aliases": aliases,
        # Paramètres de projection : tout point géographique peut être placé
        # dans le même repère que les tracés.
        "projection": {"minLon": round(minx, 5), "maxLat": round(maxy, 5),
                       "scale": round(scale, 5)},
        "provinceBoxes": province_boxes,
        "landmarks": landmarks,
        "zones": zones,
    }
    out_overview = os.path.join(ROOT, "site", "geo", "zones-overview.json")
    os.makedirs(os.path.dirname(out_overview), exist_ok=True)
    io.open(out_overview, "w", encoding="utf-8", newline="\n").write(
        json.dumps(overview, ensure_ascii=False, separators=(",", ":")))
    print("  %d tracés, %.0f Ko -> site/geo/zones-overview.json"
          % (len(zones), os.path.getsize(out_overview) / 1024))

    print("\n4. Cartes de province")

    def bounds_of(shape):
        xs = [p[0] for p in shape.points]
        ys = [p[1] for p in shape.points]
        return min(xs), min(ys), max(xs), max(ys)

    province_maps = {}
    for province_name in sorted(affected_provinces_names(config, latest)):
        own = [(rec, shape) for rec, shape in records
               if normalise(rec["PROVINCE"]) == normalise(province_name)]
        if not own:
            continue
        xs = [p[0] for _rec, shape in own for p in shape.points]
        ys = [p[1] for _rec, shape in own for p in shape.points]
        pad_x = (max(xs) - min(xs)) * PROVINCE_MARGIN
        pad_y = (max(ys) - min(ys)) * PROVINCE_MARGIN
        west, east = min(xs) - pad_x, max(xs) + pad_x
        south, north = min(ys) - pad_y, max(ys) + pad_y

        # Pas de mise au carre : c'est le viewBox qui porte les proportions,
        # comme sur la carte du pays. Un cadre carre autour d'une province
        # large ne ferait qu'ajouter deux bandes vides.

        scale = OVERVIEW_WIDTH / (east - west)
        height = round((north - south) * scale, 1)

        drawn = []
        for rec, shape in records:
            left, bottom, right, top = bounds_of(shape)
            if right < west or left > east or top < south or bottom > north:
                continue   # entierement hors du cadre
            inside = normalise(rec["PROVINCE"]) == normalise(province_name)
            tolerance = TOL_PROVINCE if inside else TOL_PROVINCE_AROUND
            subpaths = []
            for ring in rings(shape):
                simple = simplify_safely(ring, tolerance)
                if simple is None:
                    continue
                subpaths.append("M" + "L".join(
                    "%.*f %.*f" % (DECIMALS_OVERVIEW, (x - west) * scale,
                                   DECIMALS_OVERVIEW, (north - y) * scale)
                    for x, y in simple) + "Z")
            if not subpaths:
                continue
            drawn.append({"name": rec["Nom"], "province": rec["PROVINCE"],
                          "key": normalise(rec["Nom"], True),
                          "inside": inside, "d": "".join(subpaths)})

        marks = []
        for place in places:
            if place.get("province") and normalise(place["province"]) != normalise(province_name):
                continue
            if not (west <= place["lon"] <= east and south <= place["lat"] <= north):
                continue
            marks.append({"name": place["name"], "kind": place["kind"],
                          "x": round((place["lon"] - west) * scale, 1),
                          "y": round((north - place["lat"]) * scale, 1)})

        province_maps[province_name] = {
            "viewBox": "0 0 %d %s" % (OVERVIEW_WIDTH, height),
            "zones": drawn,
            "landmarks": marks,
        }
        inside_count = sum(1 for z in drawn if z["inside"])
        print("  %-13s %3d zones (%d dans la province), %d repere(s)"
              % (province_name, len(drawn), inside_count, len(marks)))

    out_maps = os.path.join(ROOT, "site", "geo", "province-maps.json")
    io.open(out_maps, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"_comment": "Traces SVG par province, produits par "
                                "scripts/build_geo.py. Ne pas modifier a la main.",
                    "maps": province_maps},
                   ensure_ascii=False, separators=(",", ":")))
    print("  %.0f Ko -> site/geo/province-maps.json"
          % (os.path.getsize(out_maps) / 1024))

    print("\n5. Polygones détaillés des provinces touchées")
    features = []
    for rec, shape in records:
        if normalise(rec["PROVINCE"]) not in affected_provinces:
            continue
        coordinates = []
        for ring in rings(shape):
            simple = simplify_safely(ring, TOL_DETAIL)
            if simple is None:
                continue
            coordinates.append([[round(x, DECIMALS_DETAIL), round(y, DECIMALS_DETAIL)]
                                for x, y in simple])
        if not coordinates:
            continue
        features.append({
            "type": "Feature",
            "properties": {"name": rec["Nom"], "province": rec["PROVINCE"],
                           "key": normalise(rec["Nom"], True)},
            "geometry": {"type": "Polygon", "coordinates": coordinates},
        })

    out_detail = os.path.join(ROOT, "data", "health-zones.geojson")
    io.open(out_detail, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"type": "FeatureCollection",
                    "note": "Zones de santé des provinces touchées, simplifiées à ~500 m. "
                            "Source HDX/OCHA, produit par scripts/build_geo.py.",
                    "features": features},
                   ensure_ascii=False, separators=(",", ":")))
    print("  %d zones dans %d provinces touchées, %.0f Ko -> data/health-zones.geojson"
          % (len(features), len(affected_provinces),
             os.path.getsize(out_detail) / 1024))

    covered = {f["properties"]["key"] for f in features}
    orphans = [z["name"] for key, z in mapping.items() if key not in covered]
    if orphans:
        print("  ! zones touchées hors des provinces exportées :", ", ".join(orphans))

    print("\nTerminé. Relancer ce script uniquement si une nouvelle province est "
          "touchée, ou pour rafraîchir la source.")


if __name__ == "__main__":
    main()
