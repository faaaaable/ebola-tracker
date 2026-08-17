#!/usr/bin/env python3
"""
Extrait, pour chaque zone de santé, un POINT REPRÉSENTATIF garanti à
l'intérieur de son polygone officiel (shapefile HDX/OCHA, 519 zones) —
plus précis qu'un géocodage par nom, qui peut mal désambiguïser un petit
hameau homonyme (voir scripts/geocode_health_zones_v2.py).

Utilise `representative_point()` de Shapely plutôt que le centroïde
géométrique : pour un polygone concave (fréquent pour des zones de santé
aux contours irréguliers), le centroïde peut tomber EN DEHORS de la forme
réelle — representative_point() garantit un point strictement à
l'intérieur.

Pour les zones non trouvées par correspondance exacte de nom, une
recherche approximative (sous-chaîne, dans la même province) propose des
candidats plutôt que d'abandonner silencieusement.

Ne modifie AUCUN fichier de données du site — diagnostic seul, à valider
avant d'appliquer à la main dans index.html (même principe que pour le
géocodage : jamais d'écrasement automatique).

Usage: python3 scripts/extract_health_zone_polygons.py
"""
import io
import zipfile

import requests
import geopandas as gpd

HDX_DATASET_ID = "dr-congo-health-0"
HDX_API_URL = f"https://data.humdata.org/api/3/action/package_show?id={HDX_DATASET_ID}"
TARGET_RESOURCE_NAME = "RDC_Zone_de_sante_09092019.zip"

# Coordonnées ACTUELLES du site (état après géocodage v1+v2).
CURRENT_COORDS = {
    "Bunia": [1.562, 30.248], "Mongbwalu": [1.937, 30.046], "Rwampara": [1.60, 30.10],
    "Nizi": [1.803, 30.378], "Lita": [1.85, 30.15], "Nyankunde": [1.30, 30.10],
    "Mangala": [1.95, 30.25], "Bambu": [1.85, 30.05],
    "Tchomia": [1.442, 30.483], "Komanda": [1.367, 29.763], "Kilo": [1.820, 30.129],
    "Fataki": [2.10, 30.30], "Damas": [1.70, 30.25], "Mandima": [1.20, 28.90],
    "Adja": [1.932, 30.676], "Drodro": [1.758, 30.556], "Aungba": [2.60, 31.05],
    "Logo": [2.60, 30.85], "Mambasa": [1.35, 29.05], "Rimba": [1.95, 30.15],
    "Ariwara": [3.134, 30.698], "Lolwa": [1.30, 28.80], "Aru": [3.02, 30.85],
    "Mahagi": [2.32, 31.03], "Kambala": [2.10, 30.85], "Boga": [1.025, 29.956],
    "Gety": [1.15, 29.85],
    "Beni": [-0.4906, 29.4664], "Butembo": [0.125, 29.292], "Goma": [-1.667, 29.226],
    "Kalunguta": [-0.4200, 29.4300], "Katwa": [0.093, 29.309], "Kyondo": [0.007, 29.397],
    "Lubero": [-0.1667, 29.2167], "Mabalako": [-0.2833, 29.3667], "Masereka": [0.0500, 29.3500],
    "Musienene": [0.0500, 29.2333], "Oicha": [0.697, 29.517], "Vuhovi": [-0.0200, 29.2600],
    "Isiro": [2.774, 27.621], "Wamba": [2.144, 27.994], "Boma Mangbetu": [2.85, 28.30],
    "Pawa": [2.4667, 27.55], "Rungu": [2.7667, 27.9667], "Gombari": [2.9333, 28.4167],
    "Bafwasende": [1.0833, 27.35], "Kabondo": [0.530, 25.223], "Lubunga": [0.486, 25.188],
    "Makiso-Kisangani": [0.515, 25.190], "Mangobo": [0.541, 25.145], "Wanie-Rukula": [0.35, 25.75],
    "Miti-Murhesa": [-2.295, 28.785],
    "Buta": [2.793, 24.729],
}

ZONE_PROVINCE = {
    "Bunia": "Ituri", "Mongbwalu": "Ituri", "Rwampara": "Ituri", "Nizi": "Ituri",
    "Lita": "Ituri", "Nyankunde": "Ituri", "Mangala": "Ituri", "Bambu": "Ituri",
    "Tchomia": "Ituri", "Komanda": "Ituri", "Kilo": "Ituri", "Fataki": "Ituri",
    "Damas": "Ituri", "Mandima": "Ituri", "Adja": "Ituri", "Drodro": "Ituri",
    "Aungba": "Ituri", "Logo": "Ituri", "Mambasa": "Ituri", "Rimba": "Ituri",
    "Ariwara": "Ituri", "Lolwa": "Ituri", "Aru": "Ituri", "Mahagi": "Ituri",
    "Kambala": "Ituri", "Boga": "Ituri", "Gety": "Ituri",
    "Beni": "Nord-Kivu", "Butembo": "Nord-Kivu", "Goma": "Nord-Kivu",
    "Kalunguta": "Nord-Kivu", "Katwa": "Nord-Kivu", "Kyondo": "Nord-Kivu",
    "Lubero": "Nord-Kivu", "Mabalako": "Nord-Kivu", "Masereka": "Nord-Kivu",
    "Musienene": "Nord-Kivu", "Oicha": "Nord-Kivu", "Vuhovi": "Nord-Kivu",
    "Isiro": "Haut-Uélé", "Wamba": "Haut-Uélé", "Boma Mangbetu": "Haut-Uélé",
    "Pawa": "Haut-Uélé", "Rungu": "Haut-Uélé", "Gombari": "Haut-Uélé",
    "Bafwasende": "Tshopo", "Kabondo": "Tshopo", "Lubunga": "Tshopo",
    "Makiso-Kisangani": "Tshopo", "Mangobo": "Tshopo", "Wanie-Rukula": "Tshopo",
    "Miti-Murhesa": "Sud-Kivu",
    "Buta": "Bas-Uélé",
}


def normalize_province(s):
    """Retire les accents pour comparer les noms de province de façon
    fiable : le shapefile écrit 'Haut-Uele'/'Bas-Uele' sans accent, alors
    qu'on attend 'Haut-Uélé'/'Bas-Uélé' — sans cette normalisation, la
    comparaison déclenche une fausse alerte "province différente" sur des
    provinces en réalité identiques."""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s.strip().lower())
        if unicodedata.category(c) != "Mn"
    )


def haversine_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def download_shapefile():
    resp = requests.get(HDX_API_URL, timeout=30,
                         headers={"User-Agent": "ebola-tracker.org script"})
    resp.raise_for_status()
    resources = resp.json()["result"]["resources"]
    url = next((r["url"] for r in resources if r.get("name") == TARGET_RESOURCE_NAME), None)
    if not url:
        url = next(r["url"] for r in resources if str(r.get("format", "")).upper() == "SHP")

    resp = requests.get(url, timeout=60, headers={"User-Agent": "ebola-tracker.org script"})
    resp.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    zf.extractall("/tmp/health_zone_shp")
    shp_name = next(n for n in zf.namelist() if n.lower().endswith(".shp"))
    return f"/tmp/health_zone_shp/{shp_name}"


def find_fuzzy_candidates(gdf, name, province):
    """Pour une zone non trouvée par correspondance exacte, cherche des
    candidats plausibles par similarité de texte (difflib, tolère les
    petites variantes : lettre insérée/manquante, espace en plus...),
    parmi les zones de la même province."""
    import difflib
    same_province = gdf[gdf["PROVINCE"].str.lower() == (province or "").lower()]
    names_in_province = same_province["Nom"].astype(str).tolist()
    return difflib.get_close_matches(name, names_in_province, n=3, cutoff=0.6)


def main():
    print("Téléchargement du shapefile officiel...")
    shp_path = download_shapefile()
    gdf = gpd.read_file(shp_path)
    print(f"{len(gdf)} zones chargées. CRS source : {gdf.crs}\n")

    if gdf.crs and str(gdf.crs).upper() != "EPSG:4326":
        print(f"Reprojection de {gdf.crs} vers WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs(4326)

    # Index par nom normalisé (minuscule, espaces normalisés) pour la
    # correspondance exacte.
    gdf["_name_norm"] = gdf["Nom"].astype(str).str.strip().str.lower()
    by_name = {row["_name_norm"]: row for _, row in gdf.iterrows()}

    print("=" * 100)
    print(f"{'Zone':<20}{'Province':<12}{'Prov. shapefile':<16}{'Ancien':<18}{'Nouveau':<18}{'km':<8}{'Statut'}")
    print("-" * 100)

    matched, unmatched = 0, []
    for name, (old_lat, old_lon) in CURRENT_COORDS.items():
        expected_province = ZONE_PROVINCE.get(name, "")
        row = by_name.get(name.strip().lower())
        if row is None:
            unmatched.append(name)
            print(f"{name:<20}{expected_province:<12}{'—':<16}{f'{old_lat:.3f},{old_lon:.3f}':<18}"
                  f"{'—':<18}{'—':<8}NON TROUVÉ")
            continue

        point = row.geometry.representative_point()
        new_lat, new_lon = point.y, point.x
        dist = haversine_km(old_lat, old_lon, new_lat, new_lon)
        shp_province = row["PROVINCE"]
        province_ok = normalize_province(shp_province) == normalize_province(expected_province)
        status = "OK" if province_ok else "! PROVINCE DIFFÉRENTE — à vérifier"
        matched += 1
        print(f"{name:<20}{expected_province:<12}{shp_province:<16}{f'{old_lat:.3f},{old_lon:.3f}':<18}"
              f"{f'{new_lat:.3f},{new_lon:.3f}':<18}{f'{dist:.1f}':<8}{status}")

    print("=" * 100)
    print(f"\n{matched}/{len(CURRENT_COORDS)} zones trouvées par correspondance exacte de nom.")

    if unmatched:
        print(f"\n{'=' * 100}")
        print(f"SUGGESTIONS POUR LES {len(unmatched)} ZONES NON TROUVÉES")
        print(f"{'=' * 100}")
        for name in unmatched:
            province = ZONE_PROVINCE.get(name, "")
            candidates = find_fuzzy_candidates(gdf, name, province)
            print(f"  {name} ({province}) : {candidates if candidates else 'aucune suggestion'}")

    print("\nAucun fichier de données modifié — diagnostic uniquement.")
    print("Chaque ligne est à comparer manuellement avant application dans index.html.")


if __name__ == "__main__":
    main()
