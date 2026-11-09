#!/usr/bin/env python3
"""
Diagnostic (pas d'extraction) : télécharge le shapefile officiel des 519
zones de santé de la RDC (HDX/OCHA) et affiche sa structure — colonnes
disponibles, quelques lignes d'exemple, et un premier test de
correspondance avec nos 53 noms de zone actuels.

But : découvrir le nom exact des champs (nom de zone, province...) avant
d'écrire le script d'extraction définitif, plutôt que de deviner — HDX
bloque les requêtes automatisées depuis l'environnement de développement,
impossible de vérifier la structure autrement qu'en la téléchargeant
réellement via ce script.

N'écrit aucun fichier de données du site.

Usage: python3 scripts/inspect_health_zone_shapefile.py
"""
import io
import sys
import zipfile

import requests
import geopandas as gpd

# Identifiant du jeu de données sur HDX (visible dans l'URL de la page :
# https://data.humdata.org/dataset/dr-congo-health-0). On passe par l'API
# CKAN d'HDX plutôt qu'un lien direct deviné : la page web humaine bloque
# les requêtes automatisées ("not available for scraping"), mais l'API est
# justement prévue pour ce type d'accès programmatique.
HDX_DATASET_ID = "dr-congo-health-0"
HDX_API_URL = f"https://data.humdata.org/api/3/action/package_show?id={HDX_DATASET_ID}"
# Nom du fichier ressource recherché dans la réponse de l'API (à défaut,
# on prend la première ressource de format SHP trouvée).
TARGET_RESOURCE_NAME = "RDC_Zone_de_sante_09092019.zip"

# Nos 53 noms de zone actuels (HEALTH_ZONE_COORDS côté site), pour un
# premier test de correspondance.
OUR_ZONE_NAMES = [
    "Bunia", "Mongbwalu", "Rwampara", "Nizi", "Lita", "Nyankunde", "Mangala",
    "Bambu", "Tchomia", "Komanda", "Kilo", "Fataki", "Damas", "Mandima",
    "Adja", "Drodro", "Aungba", "Logo", "Mambasa", "Rimba", "Ariwara",
    "Lolwa", "Aru", "Mahagi", "Kambala", "Boga", "Gety", "Beni", "Butembo",
    "Goma", "Kalunguta", "Katwa", "Kyondo", "Lubero", "Mabalako", "Masereka",
    "Musienene", "Oicha", "Vuhovi", "Isiro", "Wamba", "Boma Mangbetu", "Pawa",
    "Rungu", "Gombari", "Bafwasende", "Kabondo", "Lubunga", "Makiso-Kisangani",
    "Mangobo", "Wanie-Rukula", "Miti-Murhesa", "Buta",
]


def find_shapefile_url():
    """Interroge l'API CKAN d'HDX pour récupérer la vraie URL de
    téléchargement de la ressource — plutôt que de deviner un lien direct,
    qui se heurte au mur anti-scraping de la page web humaine."""
    print(f"Requête API CKAN : {HDX_API_URL}")
    resp = requests.get(HDX_API_URL, timeout=30,
                         headers={"User-Agent": "ebola-tracker.org script diagnostic"})
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"L'API a répondu mais signale un échec : {payload}")

    resources = payload["result"]["resources"]
    print(f"{len(resources)} ressource(s) trouvée(s) dans ce dataset :")
    for r in resources:
        print(f"  - {r.get('name')} ({r.get('format')}) -> {r.get('url')}")

    # Cherche d'abord la ressource exactement nommée, sinon la première en
    # format SHP.
    for r in resources:
        if r.get("name") == TARGET_RESOURCE_NAME:
            return r["url"]
    for r in resources:
        if str(r.get("format", "")).upper() == "SHP":
            return r["url"]
    raise RuntimeError("Aucune ressource SHP trouvée dans ce dataset.")


def main():
    try:
        shapefile_url = find_shapefile_url()
    except Exception as e:
        print(f"\n! Échec de la requête API CKAN : {e}")
        print("  Va sur https://data.humdata.org/dataset/dr-congo-health-0 dans un vrai")
        print("  navigateur pour vérifier manuellement l'identifiant du dataset et le nom")
        print("  de la ressource, puis ajuste HDX_DATASET_ID / TARGET_RESOURCE_NAME.")
        return 1

    print(f"\nURL de téléchargement trouvée : {shapefile_url}")
    print("Téléchargement...")
    try:
        resp = requests.get(shapefile_url, timeout=60,
                             headers={"User-Agent": "ebola-tracker.org script diagnostic"})
        resp.raise_for_status()
    except Exception as e:
        print(f"\n! Échec du téléchargement : {e}")
        return 1

    print(f"Téléchargé : {len(resp.content) / 1024:.0f} Ko\n")

    try:
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
    except zipfile.BadZipFile:
        print("! Le fichier téléchargé n'est pas un zip valide (probablement une page")
        print("  d'erreur HTML plutôt que le fichier). Vérifie l'URL manuellement.")
        return 1

    shp_names = [n for n in zf.namelist() if n.lower().endswith(".shp")]
    print(f"Contenu du zip : {zf.namelist()}")
    if not shp_names:
        print("! Aucun fichier .shp trouvé dans l'archive.")
        return 1

    zf.extractall("/tmp/health_zone_shp")
    shp_path = f"/tmp/health_zone_shp/{shp_names[0]}"

    print(f"\nChargement de {shp_path} avec geopandas...")
    gdf = gpd.read_file(shp_path)

    print(f"\n{'=' * 70}")
    print(f"{len(gdf)} entités chargées.")
    print(f"Colonnes disponibles : {list(gdf.columns)}")
    print(f"{'=' * 70}\n")

    print("Aperçu des 5 premières lignes (colonnes non-géométrie) :")
    print(gdf.drop(columns="geometry").head(5).to_string())

    # Test de correspondance : cherche un champ candidat contenant les noms
    # de zone (le nom exact du champ varie selon la source), et voit combien
    # de nos 53 zones s'y retrouvent (comparaison insensible à la casse).
    print(f"\n{'=' * 70}")
    print("TEST DE CORRESPONDANCE avec nos 53 zones actuelles")
    print(f"{'=' * 70}")
    candidate_cols = [c for c in gdf.columns if c.lower() not in ("geometry",)]
    for col in candidate_cols:
        try:
            values_lower = set(str(v).strip().lower() for v in gdf[col].dropna())
        except Exception:
            continue
        matches = [name for name in OUR_ZONE_NAMES if name.lower() in values_lower]
        if len(matches) >= 5:  # seuil arbitraire pour ne montrer que les colonnes pertinentes
            print(f"\nColonne '{col}' : {len(matches)}/{len(OUR_ZONE_NAMES)} zones trouvées")
            missing = [n for n in OUR_ZONE_NAMES if n not in matches]
            print(f"  Non trouvées ({len(missing)}) : {missing}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
