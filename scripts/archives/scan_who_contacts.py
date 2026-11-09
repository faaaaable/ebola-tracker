#!/usr/bin/env python3
"""
Diagnostic : vérifie si les Weekly External Situation Report de l'OMS
(reports/who/*.pdf) contiennent une donnée équivalente au "taux de suivi
des contacts" des SitRep INSP — pour voir si on peut compléter les trous
de data/contacts-followup.json avec cette source secondaire.

Les rapports OMS sont en anglais, d'où une regex différente de celle
utilisée pour les SitRep INSP (contacts-followup.json).

Ne modifie aucune donnée — sortie purement informative.

Usage: python3 scripts/scan_who_contacts.py
"""
import glob
import os
import re

import pdfplumber

WHO_REPORTS_DIR = "reports/who"

# Termes anglais plausibles pour ce genre de métrique dans un rapport OMS —
# volontairement large, on affine une fois qu'on sait ce qui apparaît
# vraiment (ou pas) dans ces documents.
CONTACTS_EN_RE = re.compile(
    r"(?:contact(?:s)?\s+(?:tracing|follow[\s-]?up|followed)|"
    r"contacts?\s+(?:are|is)?\s*(?:currently\s+)?under\s+follow[\s-]?up|"
    r"proportion of contacts|percentage of contacts|"
    r"contacts?\s+(?:seen|traced|monitored))"
    r".{0,100}?(\d[\d.,]*)\s*%",
    re.IGNORECASE | re.DOTALL,
)


def main():
    pdfs = sorted(glob.glob(os.path.join(WHO_REPORTS_DIR, "*.pdf")))
    print(f"{len(pdfs)} PDF trouvé(s) dans {WHO_REPORTS_DIR}/\n")

    if not pdfs:
        print("Aucun fichier trouvé — vérifie que reports/who/ existe bien "
              "et contient les PDF déjà téléchargés.")
        return

    found = 0
    for pdf_path in pdfs:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        except Exception as e:
            print(f"  ! {os.path.basename(pdf_path)} : erreur de lecture ({e})")
            continue

        m = CONTACTS_EN_RE.search(full_text)
        name = os.path.basename(pdf_path)
        if m:
            found += 1
            # Affiche un peu de contexte autour du match pour vérifier
            # manuellement que ça correspond bien à la bonne métrique.
            start = max(0, m.start() - 40)
            end = min(len(full_text), m.end() + 20)
            context = full_text[start:end].replace("\n", " ")
            print(f"  ✓ {name} : {m.group(1)}%  —  \"...{context}...\"")
        else:
            print(f"  ✗ {name} : rien trouvé")

    print()
    print(f"Total : {found}/{len(pdfs)} rapport(s) OMS avec une donnée exploitable.")


if __name__ == "__main__":
    main()
