#!/usr/bin/env python3
"""
Géocode chaque zone de santé de HEALTH_ZONE_COORDS via Nominatim
(OpenStreetMap), et produit un RAPPORT comparant l'ancienne coordonnée
(estimée à la main) et la nouvelle (géocodée), avec la distance entre les
deux. N'écrit AUCUN fichier de données du site — ce script sert seulement
au diagnostic, pour que chaque changement soit revu avant d'être appliqué,
plutôt que d'écraser silencieusement des coordonnées.

Respecte la politique d'usage de Nominatim (1 requête/seconde, User-Agent
identifiable) : https://operations.osmfoundation.org/policies/nominatim/

Toute coordonnée renvoyée hors des frontières approximatives de la RDC est
rejetée (résultat probablement erroné : homonyme ailleurs, désambiguïsation
ratée) plutôt que d'être proposée.

Usage: python3 scripts/geocode_health_zones.py
"""
import json
import time
import urllib.parse
import urllib.request

# Coordonnées actuelles du site, copiées depuis HEALTH_ZONE_COORDS
# dans index.html (à tenir synchronisé manuellement si la liste évolue).
CURRENT_COORDS = {
    "Bunia": [1.567, 30.250], "Mongbwalu": [1.933, 30.033], "Rwampara": [1.60, 30.10],
    "Nizi": [1.75, 30.35], "Lita": [1.85, 30.15], "Nyankunde": [1.30, 30.10],
    "Mangala": [1.95, 30.25], "Bambu": [1.85, 30.05],
    "Tchomia": [1.40, 30.55], "Komanda": [1.383, 29.783], "Kilo": [1.90, 30.05],
    "Fataki": [2.10, 30.30], "Damas": [1.70, 30.25], "Mandima": [1.20, 28.90],
    "Adja": [1.95, 30.55], "Drodro": [1.75, 30.50], "Aungba": [2.60, 31.05],
    "Logo": [2.60, 30.85], "Mambasa": [1.35, 29.05], "Rimba": [1.95, 30.15],
    "Ariwara": [3.05, 30.75], "Lolwa": [1.30, 28.80], "Aru": [3.02, 30.85],
    "Mahagi": [2.32, 31.03], "Kambala": [2.10, 30.85], "Boga": [0.95, 29.95],
    "Gety": [1.15, 29.85],
    "Beni": [-0.4906, 29.4664], "Butembo": [0.1500, 29.2833], "Goma": [-1.6792, 29.2228],
    "Kalunguta": [-0.4200, 29.4300], "Katwa": [0.0800, 29.2800], "Kyondo": [0.0200, 29.4500],
    "Lubero": [-0.1667, 29.2167], "Mabalako": [-0.2833, 29.3667], "Masereka": [0.0500, 29.3500],
    "Musienene": [0.0500, 29.2333], "Oicha": [0.6667, 29.5167], "Vuhovi": [-0.0200, 29.2600],
    "Isiro": [2.7833, 27.6167], "Wamba": [2.1500, 27.9833], "Boma Mangbetu": [2.85, 28.30],
    "Pawa": [2.4667, 27.55], "Rungu": [2.7667, 27.9667], "Gombari": [2.9333, 28.4167],
    "Bafwasende": [1.0833, 27.35], "Kabondo": [0.5000, 25.1667], "Lubunga": [0.4833, 25.15],
    "Makiso-Kisangani": [0.5167, 25.20], "Mangobo": [0.5333, 25.2333], "Wanie-Rukula": [0.35, 25.75],
    "Miti-Murhesa": [-2.35, 28.75],
    "Buta": [2.795, 24.734],
}

# Frontières approximatives de la RDC (mêmes bornes que DRC_BOUNDS côté site)
DRC_LAT_RANGE = (-13.459, 5.386)
DRC_LON_RANGE = (12.204, 33.2)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ebola-tracker.org geocoding script (contact via github.com/faaaaable/ebola-tracker)"


def haversine_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def geocode(name):
    params = {
        "q": f"{name}, République Démocratique du Congo",
        "format": "json",
        "countrycodes": "cd",
        "limit": 1,
    }
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None, str(e)
    if not data:
        return None, "aucun résultat"
    lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    if not (DRC_LAT_RANGE[0] <= lat <= DRC_LAT_RANGE[1] and DRC_LON_RANGE[0] <= lon <= DRC_LON_RANGE[1]):
        return None, f"hors RDC ({lat:.3f},{lon:.3f}) — résultat rejeté"
    return (lat, lon), data[0].get("display_name", "")


def main():
    print(f"Géocodage de {len(CURRENT_COORDS)} zones via Nominatim (1 req/s)...\n")
    print("=" * 100)
    print(f"{'Zone':<22}{'Ancien (lat,lon)':<22}{'Nouveau (lat,lon)':<22}{'Écart (km)':<12}{'Détail'}")
    print("-" * 100)

    results = []
    for name, (old_lat, old_lon) in CURRENT_COORDS.items():
        coord, detail = geocode(name)
        if coord is None:
            print(f"{name:<22}{f'{old_lat:.3f},{old_lon:.3f}':<22}{'—':<22}{'—':<12}{detail}")
        else:
            new_lat, new_lon = coord
            dist = haversine_km(old_lat, old_lon, new_lat, new_lon)
            flag = " <-- écart important" if dist > 15 else ""
            print(f"{name:<22}{f'{old_lat:.3f},{old_lon:.3f}':<22}"
                  f"{f'{new_lat:.3f},{new_lon:.3f}':<22}{f'{dist:.1f}':<12}{detail[:40]}{flag}")
            results.append({
                "name": name, "old": [old_lat, old_lon], "new": [round(new_lat, 4), round(new_lon, 4)],
                "distance_km": round(dist, 1), "matched": detail,
            })
        time.sleep(1)  # politique d'usage Nominatim : 1 requête/seconde max

    print("=" * 100)
    print(f"\n{len(results)} zone(s) géocodée(s) avec succès sur {len(CURRENT_COORDS)}.")
    print("Aucun fichier de données modifié — ce script est un diagnostic uniquement.")
    print("Revoir chaque ligne avant d'appliquer un changement de coordonnée.")


if __name__ == "__main__":
    main()
