#!/usr/bin/env python3
"""
Télécharge automatiquement tous les SitRep MVE (Ebola RDC 2026) publiés
sur insp.cd/category/sitrep/, page par page, en décodant le lien PDF
intégré dans le lecteur embarqué de chaque article.

Usage :
    pip install requests beautifulsoup4
    python download_all_sitreps.py

Les PDF sont enregistrés dans ./reports/ (créé si besoin), avec un nom
du type SITREP_MVE_090.pdf (numéro extrait du titre de l'article).
Un fichier reports/_index.json est aussi écrit avec les métadonnées
(numéro, titre, date, URL source, nom de fichier local) — pratique pour
générer ensuite la section "reports" de data/latest.json.

Le script est idempotent : un PDF déjà présent dans reports/ n'est pas
retéléchargé (sauf avec --force).
"""

import argparse
import base64
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

BASE = "https://insp.cd"
LISTING_URL = f"{BASE}/category/sitrep/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; sitrep-archiver/1.0; +https://insp.cd/)"
}
OUT_DIR = Path("reports")
INDEX_PATH = OUT_DIR / "_index.json"

SITREP_NUM_RE = re.compile(r"N[°O]?\s*0*(\d{1,3})", re.IGNORECASE)


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def discover_listing_pages() -> list[str]:
    """Renvoie l'URL de chaque page de pagination de la catégorie SitRep."""
    soup = get_soup(LISTING_URL)
    pages = {LISTING_URL}
    for a in soup.select("a[href*='/category/sitrep/page/']"):
        href = a.get("href")
        if href:
            pages.add(urljoin(BASE, href))
    # Trie par numéro de page croissant (LISTING_URL = page 1 en premier)
    def page_num(u: str) -> int:
        m = re.search(r"/page/(\d+)/?", u)
        return int(m.group(1)) if m else 1
    return sorted(pages, key=page_num)


def article_links_from_listing(url: str) -> list[tuple[str, str]]:
    """Renvoie [(titre, url_article), ...] pour une page de listing donnée."""
    soup = get_soup(url)
    results = []
    for h in soup.select("h3 a, h2 a"):
        title = h.get_text(strip=True)
        href = h.get("href")
        if href and "sitrep" in title.lower():
            results.append((title, urljoin(BASE, href)))
    return results


def extract_pdf_url_from_article(article_url: str) -> str | None:
    """
    Cherche le lien du lecteur PDF embarqué (paramètre pdfemb-data en
    base64 JSON contenant la vraie URL du fichier), et retombe sur un
    lien <a href="....pdf"> classique si le site change de format.
    """
    resp = requests.get(article_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # 1) motif pdfemb-data=<base64 json avec "url": "...">
    for m in re.finditer(r"pdfemb-data=([A-Za-z0-9+/=]+)", html):
        token = m.group(1)
        try:
            padded = token + "=" * (-len(token) % 4)
            decoded = base64.b64decode(padded).decode("utf-8", errors="ignore")
            data = json.loads(decoded)
            if "url" in data:
                return data["url"]
        except Exception:
            continue

    # 2) repli : lien direct vers un .pdf dans le HTML
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("a[href$='.pdf']"):
        return urljoin(BASE, a["href"])

    return None


def guess_sitrep_number(title: str) -> str:
    m = SITREP_NUM_RE.search(title)
    if m:
        return m.group(1).zfill(3)
    # repli : hash court du titre si aucun numéro trouvé
    return re.sub(r"\W+", "_", title)[:20]


def download_pdf(pdf_url: str, dest: Path, force: bool = False) -> bool:
    if dest.exists() and not force:
        return False
    resp = requests.get(pdf_url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                         help="Retélécharge même les PDF déjà présents")
    parser.add_argument("--max-pages", type=int, default=None,
                         help="Limite le nombre de pages de listing parcourues (debug)")
    parser.add_argument("--sleep", type=float, default=0.5,
                         help="Pause en secondes entre deux requêtes (politesse envers le serveur)")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    index: dict[str, dict] = {}
    if INDEX_PATH.exists():
        try:
            index = json.loads(INDEX_PATH.read_text())
        except Exception:
            index = {}

    print(f"Découverte des pages de listing sur {LISTING_URL} ...")
    listing_pages = discover_listing_pages()
    if args.max_pages:
        listing_pages = listing_pages[: args.max_pages]
    print(f"{len(listing_pages)} page(s) de listing trouvée(s).")

    all_articles: list[tuple[str, str]] = []
    for page_url in listing_pages:
        print(f"  -> {page_url}")
        all_articles.extend(article_links_from_listing(page_url))
        time.sleep(args.sleep)

    print(f"\n{len(all_articles)} article(s) SitRep trouvé(s) au total.\n")

    downloaded, skipped, failed = 0, 0, 0
    for title, article_url in all_articles:
        num = guess_sitrep_number(title)
        dest = OUT_DIR / f"SITREP_MVE_{num}.pdf"
        try:
            pdf_url = extract_pdf_url_from_article(article_url)
            if not pdf_url:
                print(f"  [!] Pas de PDF trouvé pour: {title} ({article_url})")
                failed += 1
                continue

            was_new = download_pdf(pdf_url, dest, force=args.force)
            index[num] = {
                "title": title,
                "article_url": article_url,
                "pdf_url": pdf_url,
                "file": str(dest),
            }
            if was_new:
                print(f"  [OK] {title} -> {dest.name}")
                downloaded += 1
            else:
                print(f"  [=]  {title} -> {dest.name} (déjà présent)")
                skipped += 1
        except Exception as e:
            print(f"  [X]  Échec pour {title} ({article_url}): {e}")
            failed += 1
        time.sleep(args.sleep)

    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True))

    print(f"\nTerminé : {downloaded} téléchargé(s), {skipped} déjà présent(s), {failed} échec(s).")
    print(f"Index écrit dans {INDEX_PATH}")


if __name__ == "__main__":
    sys.exit(main())
