#!/usr/bin/env python3
"""
Vérifie quotidiennement si un nouveau bilan officiel (SITREP) de l'épidémie
Ebola-Bundibugyo en RDC a été publié, en interrogeant les sources officielles
via l'API Claude (avec l'outil de recherche web).

Ce script NE PUBLIE JAMAIS automatiquement de nouvelles données : il écrit
un fichier de proposition (data/sitreps.proposed.json) qui n'est intégré
au site qu'après validation humaine, via une Pull Request GitHub.

Variables d'environnement requises :
  ANTHROPIC_API_KEY : clé API Anthropic (stockée en secret GitHub Actions)
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sitreps.json"
PROPOSED_PATH = Path(__file__).resolve().parent.parent / "data" / "sitreps.proposed.json"

SOURCES = [
    "https://sante.gouv.cd/epidemie/ebola-bundibugyo-2026",
    "https://bsp.insp.cd/",
    "https://www.who.int/emergencies/situations/ebola-outbreak---drc-2026",
]

SYSTEM_PROMPT = f"""Tu es un assistant de veille épidémiologique. Ta seule tâche est de
vérifier si un nouveau bilan officiel (SITREP) de l'épidémie Ebola-Bundibugyo 2026 en RDC
a été publié depuis la dernière entrée connue, en consultant en priorité ces sources
officielles : {', '.join(SOURCES)}.

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
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    stop_reason = data.get("stop_reason")
    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    raw = "\n".join(text_blocks).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    if not raw:
        # Réponse sans bloc de texte exploitable (ex : coupée avant la fin, ou
        # entièrement composée de blocs d'outil). On log le contenu complet pour
        # diagnostic, et on traite ça comme "rien trouvé" plutôt que de planter.
        print(f"Réponse sans texte exploitable (stop_reason={stop_reason}). Contenu complet :")
        print(json.dumps(data.get("content", []), ensure_ascii=False, indent=2))
        return {"new_data_found": False, "entry": None}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"Réponse non-JSON reçue (stop_reason={stop_reason}). Contenu brut :")
        print(raw)
        return {"new_data_found": False, "entry": None}


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
