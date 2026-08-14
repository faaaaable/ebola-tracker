#!/usr/bin/env python3
"""
Vérifie quotidiennement si un nouveau bilan officiel (SITREP) de l'épidémie
Ebola-Bundibugyo en RDC a été publié, en interrogeant les sources officielles
via l'API Claude (avec les outils de recherche et de récupération web).

Ce script NE PUBLIE JAMAIS de données sans passer par le fichier de sortie
data/sitreps.proposed.json — c'est le workflow GitHub Actions qui décide
ensuite s'il publie automatiquement ou non.

Variables d'environnement requises :
  ANTHROPIC_API_KEY : clé API Anthropic (stockée en secret GitHub Actions)
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sitreps.json"
PROPOSED_PATH = Path(__file__).resolve().parent.parent / "data" / "sitreps.proposed.json"

# Page qui liste les SitRep les plus récents en premier (numérotés) — c'est la
# source la plus fiable pour détecter rapidement l'existence d'un nouveau SitRep.
PRIMARY_SOURCE = "https://insp.cd/ebola-17eme-epidemie/"

SOURCES = [
    PRIMARY_SOURCE,
    "https://insp.cd/sitrep/",
    "https://sante.gouv.cd/epidemie/ebola-bundibugyo-2026",
    "https://bsp.insp.cd/",
    "https://www.who.int/emergencies/situations/ebola-outbreak---drc-2026",
]

SYSTEM_PROMPT = f"""Tu es un assistant de veille épidémiologique. Ta seule tâche est de
vérifier si un nouveau bilan officiel (SITREP) de l'épidémie Ebola-Bundibugyo 2026 en RDC
a été publié depuis la dernière entrée connue.

ÉTAPE OBLIGATOIRE — à faire en premier, avant toute autre recherche :
Utilise l'outil web_fetch (pas seulement web_search) pour charger directement le contenu
réel et à jour de {PRIMARY_SOURCE} (ou {SOURCES[1]} si la première est inaccessible).
web_search seul peut renvoyer des résultats obsolètes ou pas encore indexés : ne te fie
JAMAIS uniquement à des extraits de recherche pour cette étape, va chercher la page
elle-même avec web_fetch. Cette page liste les SitRep numérotés du plus récent au plus
ancien (ex: "SitRep N°090/MVEBDB/12/08/2026"). Identifie le numéro et la date du SitRep
le plus récent qui y figure.

C'est la référence prioritaire : ignore toute source secondaire (ECDC, CGTN, Wikipedia,
presse, etc.) tant que tu n'as pas vérifié cette page en premier avec web_fetch — ces
sources secondaires peuvent avoir plusieurs jours de retard sur les SitRep INSP, et un
SitRep peut exister sur insp.cd sans être encore repris ailleurs.

Si le SitRep le plus récent trouvé sur insp.cd est plus récent que la dernière entrée
connue, utilise web_fetch pour accéder au contenu du PDF correspondant et en extraire les
chiffres (cas confirmés, décès, guéris). Si le PDF n'est pas exploitable mais que d'autres
sources officielles (ministère, OMS) confirment déjà les mêmes chiffres pour cette date,
tu peux les utiliser en le précisant dans "notes".

Sources officielles à consulter, dans cet ordre de priorité : {', '.join(SOURCES)}.

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte avant ou après, sans balises
Markdown, au format suivant :

{{
  "new_data_found": true ou false,
  "entry": {{ "date": "AAAA-MM-JJ", "confirmed": nombre, "deaths": nombre ou null, "recovered": nombre ou null }},
  "source_url": "URL exacte de la page consultée",
  "confidence": "high" ou "medium" ou "low",
  "notes": "brève explication en français"
}}

Si aucune donnée plus récente que la dernière entrée fournie n'est trouvée, ou si tu n'es
pas au moins en confiance 'medium', renvoie new_data_found: false et entry: null."""


def load_existing_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_json_object(text):
    """Extrait le premier objet JSON valide trouvé dans un texte, même s'il est
    précédé ou suivi d'autre texte (le modèle ne respecte pas toujours à la
    lettre la consigne "réponds uniquement en JSON")."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        start = match.start()
        try:
            obj, _ = decoder.raw_decode(text, start)
            return obj
        except json.JSONDecodeError:
            continue
    return None


def call_claude_api(latest_entry):
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Dernière entrée connue : {json.dumps(latest_entry, ensure_ascii=False)}. "
                    "Vérifie s'il existe un bilan plus récent sur les sources officielles."
                ),
            }
        ],
        "tools": [
            {"type": "web_search_20250305", "name": "web_search"},
            {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 10},
        ],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            # Requis pour activer l'outil web_fetch (encore en bêta).
            "anthropic-beta": "web-fetch-2025-09-10",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    stop_reason = data.get("stop_reason")
    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    raw = "\n".join(text_blocks).strip()

    if not raw:
        print(f"Réponse sans texte exploitable (stop_reason={stop_reason}). Contenu complet :")
        print(json.dumps(data.get("content", []), ensure_ascii=False, indent=2))
        return {"new_data_found": False, "entry": None}

    parsed = extract_json_object(raw)
    if parsed is None:
        print(f"Aucun objet JSON exploitable trouvé (stop_reason={stop_reason}). Contenu brut :")
        print(raw)
        return {"new_data_found": False, "entry": None}

    if raw.strip() != json.dumps(parsed, ensure_ascii=False):
        # Le modèle a ajouté du texte autour du JSON : on le garde quand même,
        # mais on log le texte complet pour audit / debug.
        print("Note : la réponse contenait du texte en plus du JSON. Texte complet conservé pour audit :")
        print(raw)

    return parsed


def main():
    if not ANTHROPIC_API_KEY:
        print("ERREUR : ANTHROPIC_API_KEY n'est pas défini.", file=sys.stderr)
        sys.exit(1)

    existing = load_existing_data()
    latest = sorted(existing, key=lambda e: e["date"])[-1]

    print(f"Dernière entrée connue : {latest}")
    result = call_claude_api(latest)
    print("Réponse de vérification :", json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("new_data_found"):
        print("Aucune nouvelle donnée trouvée. Rien à proposer.")
        return

    entry = result["entry"]
    if entry["date"] == latest["date"]:
        print("La date la plus récente trouvée correspond déjà aux données existantes.")
        return

    updated = existing + [entry]
    with open(PROPOSED_PATH, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print(f"Nouvelle entrée proposée et écrite dans {PROPOSED_PATH}")


if __name__ == "__main__":
    main()
