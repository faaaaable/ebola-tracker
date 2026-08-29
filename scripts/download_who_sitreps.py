#!/usr/bin/env python3
"""
Télécharge les "Weekly External Situation Report" de l'OMS (Bureau régional
Afrique) sur l'épidémie Ebola Bundibugyo RDC/Ouganda, depuis les liens
directs IRIS (bibliothèque numérique de l'OMS) — trouvés un par un via
recherche web, pas via un flux structuré.

Stocké séparément des SitRep INSP (reports/who/ plutôt que reports/),
puisque c'est une source différente et indépendante.

ATTENTION : la correspondance numéro de rapport ↔ date pour 06 à 12 n'a
PAS été vérifiée individuellement (contrairement à 01-05 et 14, où le
contenu de la page a été lu directement) — les liens ont été fournis en
bloc par l'utilisateur, dans un ordre supposé chronologique croissant.
Le rapport 13 (09 août 2026), longtemps introuvable, a été retrouvé le 29 août via l'API de recherche d'IRIS, comme le 15.
Vérifier le contenu de chaque PDF après téléchargement avant de s'appuyer
dessus pour une extraction automatisée.

Usage: python3 scripts/download_who_sitreps.py
"""
import os
import re
import urllib.request

OUTPUT_DIR = "reports/who"
USER_AGENT = "ebola-tracker.org (contact via github.com/faaaaable/ebola-tracker)"

# (numéro, date de rapportage, URL de téléchargement IRIS)
# Numéros/dates 01-05 et 14 confirmés en lisant le contenu de chaque page
# afro.who.int correspondante. 06-12 : correspondance supposée d'après
# l'ordre de collage, à vérifier. 13 et 15 : trouvés via l'API IRIS, vérifiés.
WHO_REPORTS = [
    ("01", "2026-05-18", "https://iris.who.int/bitstreams/bb1d4668-04e0-4563-b7c4-d1bdefbc9f05/download"),
    ("02", "2026-05-24", "https://iris.who.int/bitstreams/4a06bc4f-6c0b-4c0d-925a-8a7b5a13299f/download"),
    ("03", "2026-05-31", "https://iris.who.int/bitstreams/2f969fbf-de50-4154-880b-ccf471b21356/download"),
    ("04", "2026-06-07", "https://iris.who.int/bitstreams/a296c3f1-0338-4a05-9ee8-6cf93ad7c292/download"),
    ("05", "2026-06-14", "https://iris.who.int/bitstreams/318f8678-54ab-4d73-9453-48857b245ad9/download"),
    ("06", "2026-06-21", "https://iris.who.int/bitstreams/9f709b11-f8ab-4d3b-aba9-9fe7fa743395/download"),  # non vérifié
    ("07", "2026-06-28", "https://iris.who.int/bitstreams/6eda0efa-73d3-42dd-900b-b75f92b6b301/download"),  # non vérifié
    ("08", "2026-07-05", "https://iris.who.int/bitstreams/0cf7f2bf-511d-409f-b47e-2b933c276ad0/download"),  # non vérifié
    ("09", "2026-07-12", "https://iris.who.int/bitstreams/46bd6014-40e9-4b5e-9046-9687ce6568c3/download"),  # non vérifié
    ("10", "2026-07-19", "https://iris.who.int/bitstreams/84ac74ed-406e-4a1b-9af0-502d24ba7c85/download"),  # non vérifié
    ("11", "2026-07-26", "https://iris.who.int/bitstreams/e5023872-6b1c-446e-992d-7c92810d730a/download"),  # non vérifié
    ("12", "2026-08-02", "https://iris.who.int/bitstreams/f608a794-47cf-4b89-9b2d-6ff41b75c2ee/download"),  # non vérifié
    # ("13", "2026-08-09", None),  # jamais retrouvé
    # 13 et 15 : retrouves le 29 aout 2026 via l'API de recherche d'IRIS
    # (iris.who.int/server/api/discover/search/objects, requete « Ebola
    # Bundibugyo "External Situation Report" 2026 », tri par date
    # d'accession) — la recherche web ne les trouvait pas. Contenu verifie
    # sur la premiere page de chaque PDF.
    ("13", "2026-08-09", "https://iris.who.int/bitstreams/21922255-8b77-4612-bc0e-1064fafcf6ef/download"),
    ("14", "2026-08-16", "https://iris.who.int/bitstreams/7884afdb-fb05-4edf-b564-6a475fed0243/download"),
    ("15", "2026-08-23", "https://iris.who.int/bitstreams/2dfa5168-2ff5-474f-829b-33b715616b1f/download"),
]


def rest_content_url(download_url):
    """Convertit une URL de téléchargement IRIS (l'interface Angular/DSpace,
    qui ne renvoie que la coquille HTML de l'application sans exécution JS)
    en URL de l'API REST DSpace sous-jacente, qui sert le fichier brut
    directement — cette dernière est censée fonctionner sans navigateur."""
    m = re.search(r"/bitstreams/([0-9a-f-]+)/download", download_url)
    if not m:
        return download_url
    bitstream_id = m.group(1)
    return f"https://iris.who.int/server/api/core/bitstreams/{bitstream_id}/content"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    downloaded, skipped, failed = 0, 0, 0

    for number, date, url in WHO_REPORTS:
        filename = f"WHO_WeeklyExtSitRep_{number}_{date}.pdf"
        path = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(path) and os.path.getsize(path) > 0:
            print(f"  [=] Rapport {number} ({date}) déjà présent, ignoré.")
            skipped += 1
            continue

        try:
            req = urllib.request.Request(rest_content_url(url), headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()
                content_type = resp.headers.get("Content-Type", "inconnu")
                status = resp.status
            if not content.startswith(b"%PDF"):
                # Diagnostic : affiche ce qui a été reçu à la place d'un PDF
                # (page de blocage anti-bot, redirection, erreur...) plutôt
                # que d'ignorer silencieusement — on ne sait pas encore
                # pourquoi ça échoue, donc pas la peine de deviner.
                snippet = content[:300].decode("utf-8", errors="replace")
                print(f"  [!] Rapport {number} ({date}) : pas un PDF. "
                      f"HTTP {status}, Content-Type: {content_type}")
                print(f"      Début de la réponse reçue : {snippet!r}")
                failed += 1
                continue
            with open(path, "wb") as f:
                f.write(content)
            print(f"  [+] Rapport {number} ({date}) téléchargé ({len(content) // 1024} Ko).")
            downloaded += 1
        except Exception as e:
            print(f"  [!] Rapport {number} ({date}) : échec du téléchargement ({e}).")
            failed += 1

    print(f"\nTerminé : {downloaded} téléchargé(s), {skipped} déjà présent(s), {failed} échec(s).")
    if failed == 0 and skipped + downloaded < 14:
        print("Rappel : le rapport N°13 (09 août 2026) n'a jamais été retrouvé, "
              "et manque donc toujours à l'appel (13 sur 14 au total).")


if __name__ == "__main__":
    main()
