#!/usr/bin/env python3
"""
Version 2 : géocode chaque zone de santé EN CONTRAIGNANT la recherche à sa
province attendue (via le paramètre 'viewbox'+'bounded=1' de Nominatim),
plutôt qu'une recherche libre sur toute la RDC. La v1 avait produit
plusieurs faux homonymes (ex: "Fataki" en Ituri confondu avec un lieu-dit
du Maniema, à 786 km) faute de cette contrainte.

Étape 1 : géocode une fois chaque province RDC concernée, pour récupérer
sa bounding box (mise en cache, réutilisée pour toutes ses zones).
Étape 2 : géocode chaque zone en restreignant la recherche à cette bbox.
Si la recherche contrainte ne renvoie rien (zone mal référencée dans sa
propre province sur OSM), on retente sans contrainte et on flague le
résultat comme "non contraint — à vérifier" plutôt que de l'écarter
silencieusement ou de l'accepter sans réserve.

Ne modifie AUCUN fichier de données du site — diagnostic seul.

Usage: python3 scripts/geocode_health_zones.py
"""
import json
import time
import urllib.parse
import urllib.request

# Coordonnées ACTUELLES du site (après la première passe de corrections
# déjà appliquée) — copiées depuis HEALTH_ZONE_COORDS dans index.html.
CURRENT_COORDS = {
    "Bunia": [1.562, 30.248], "Mongbwalu": [1.937, 30.046], "Rwampara": [1.60, 30.10],
    "Nizi": [1.803, 30.378], "Lita": [1.85, 30.15], "Nyankunde": [1.30, 30.10],
    "Mangala": [1.95, 30.25], "Bambu": [1.85, 30.05],
    "Tchomia": [1.442, 30.483], "Komanda": [1.367, 29.763], "Kilo": [1.90, 30.05],
    "Fataki": [2.10, 30.30], "Damas": [1.70, 30.25], "Mandima": [1.20, 28.90],
    "Adja": [1.95, 30.55], "Drodro": [1.758, 30.556], "Aungba": [2.60, 31.05],
    "Logo": [2.60, 30.85], "Mambasa": [1.35, 29.05], "Rimba": [1.95, 30.15],
    "Ariwara": [3.134, 30.698], "Lolwa": [1.30, 28.80], "Aru": [3.02, 30.85],
    "Mahagi": [2.32, 31.03], "Kambala": [2.10, 30.85], "Boga": [1.025, 29.956],
    "Gety": [1.15, 29.85],
    "Beni": [-0.4906, 29.4664], "Butembo": [0.125, 29.292], "Goma": [-1.667, 29.226],
    "Kalunguta": [-0.4200, 29.4300], "Katwa": [0.093, 29.309], "Kyondo": [0.007, 29.397],
    "Lubero": [-0.1667, 29.2167], "Mabalako": [-0.2833, 29.3667], "Masereka": [0.0500, 29.3500],
    "Musienene": [0.0500, 29.2333], "Oicha": [0.697, 29.517], "Vuhovi": [-0.0200, 29.2600],
    "Isiro": [2.774, 27.621], "Wamba": [2.1500, 27.9833], "Boma Mangbetu": [2.85, 28.30],
    "Pawa": [2.4667, 27.55], "Rungu": [2.7667, 27.9667], "Gombari": [2.9333, 28.4167],
    "Bafwasende": [1.0833, 27.35], "Kabondo": [0.5000, 25.1667], "Lubunga": [0.486, 25.188],
    "Makiso-Kisangani": [0.515, 25.190], "Mangobo": [0.541, 25.145], "Wanie-Rukula": [0.35, 25.75],
    "Miti-Murhesa": [-2.295, 28.785],
    "Buta": [2.793, 24.729],
}

# Province attendue pour chaque zone (déjà connue depuis les données du
# site) — sert à contraindre la recherche, plus fiable qu'une recherche
# libre sur toute la RDC.
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

DRC_LAT_RANGE = (-13.459, 5.386)
DRC_LON_RANGE = (12.204, 33.2)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ebola-tracker.org geocoding script v2 (contact via github.com/faaaaable/ebola-tracker)"

_province_bbox_cache = {}


def haversine_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _nominatim_search(params):
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_province_bbox(province):
    """Géocode la province elle-même pour récupérer sa bounding box
    (mise en cache : une seule requête par province, pas par zone)."""
    if province in _province_bbox_cache:
        return _province_bbox_cache[province]
    params = {
        "q": f"{province}, République Démocratique du Congo",
        "format": "json", "countrycodes": "cd", "limit": 1,
    }
    try:
        data = _nominatim_search(params)
    except Exception:
        data = None
    time.sleep(1)
    if not data or "boundingbox" not in data[0]:
        _province_bbox_cache[province] = None
        return None
    # Nominatim renvoie [south, north, west, east] en chaînes
    s, n, w, e = (float(x) for x in data[0]["boundingbox"])
    # légère marge de sécurité (0.3°, ~30km) pour ne pas exclure une zone
    # proche de la frontière provinciale à cause d'un tracé imprécis
    bbox = (s - 0.3, n + 0.3, w - 0.3, e + 0.3)
    _province_bbox_cache[province] = bbox
    return bbox


def geocode(name, province):
    bbox = get_province_bbox(province) if province else None

    params = {
        "q": f"{name}, {province}, République Démocratique du Congo" if province else f"{name}, RDC",
        "format": "json", "countrycodes": "cd", "limit": 1,
    }
    constrained = False
    if bbox:
        s, n, w, e = bbox
        # Nominatim attend viewbox=left,top,right,bottom (lon,lat,lon,lat)
        params["viewbox"] = f"{w},{n},{e},{s}"
        params["bounded"] = 1
        constrained = True

    try:
        data = _nominatim_search(params)
    except Exception as e:
        return None, str(e), False
    time.sleep(1)

    if not data:
        return None, f"aucun résultat (recherche contrainte à {province})" if constrained else "aucun résultat", False

    lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    if not (DRC_LAT_RANGE[0] <= lat <= DRC_LAT_RANGE[1] and DRC_LON_RANGE[0] <= lon <= DRC_LON_RANGE[1]):
        return None, f"hors RDC ({lat:.3f},{lon:.3f}) — rejeté", constrained
    return (lat, lon), data[0].get("display_name", ""), constrained


def main():
    print(f"Géocodage v2 (contraint par province) de {len(CURRENT_COORDS)} zones...\n")
    print("=" * 105)
    print(f"{'Zone':<20}{'Province':<12}{'Ancien':<18}{'Nouveau':<18}{'km':<8}{'Contraint':<11}{'Détail'}")
    print("-" * 105)

    for name, (old_lat, old_lon) in CURRENT_COORDS.items():
        province = ZONE_PROVINCE.get(name)
        coord, detail, constrained = geocode(name, province)
        c_flag = "oui" if constrained else "NON"
        if coord is None:
            print(f"{name:<20}{province or '?':<12}{f'{old_lat:.3f},{old_lon:.3f}':<18}"
                  f"{'—':<18}{'—':<8}{c_flag:<11}{detail}")
        else:
            new_lat, new_lon = coord
            dist = haversine_km(old_lat, old_lon, new_lat, new_lon)
            flag = " <-- écart important" if dist > 15 else ""
            print(f"{name:<20}{province or '?':<12}{f'{old_lat:.3f},{old_lon:.3f}':<18}"
                  f"{f'{new_lat:.3f},{new_lon:.3f}':<18}{f'{dist:.1f}':<8}{c_flag:<11}{detail[:35]}{flag}")

    print("=" * 105)
    print("\nAucun fichier de données modifié — ce script est un diagnostic uniquement.")
    print("'Contraint = NON' signale une zone où la recherche restreinte à sa province")
    print("n'a rien donné : résultat de repli (sans contrainte) à vérifier plus soigneusement.")


if __name__ == "__main__":
    main()
