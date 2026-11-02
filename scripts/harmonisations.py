"""Les harmonisations de donnees annoncees par les bulletins
(data/harmonisations.json, 1er novembre 2026).

Au SitRep 169 (30 octobre 2026), l'Ituri redistribue ses cas entre ses zones
sans changer le total de la province. Les cumuls publies restent tels quels
partout ou le site les affiche ; seuls les ECARTS entre deux dates qui
encadrent l'harmonisation doivent en retrancher l'ajustement de chaque zone,
sans quoi Rwampara gagnerait 70 cas en un jour pour 5 annonces.

`rebaser` remet les instantanes anterieurs sur la base harmonisee (cumul +
ajustement) : tout ecart calcule ensuite ne compte que les vrais nouveaux
cas. A n'employer que pour des ecarts, jamais pour afficher un cumul passe.
Meme regle cote navigateur : ajustementZone (assets/js/app.js)."""
import copy
import json
import os

CHEMIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "harmonisations.json")


def charger():
    try:
        with open(CHEMIN, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in d.items() if not k.startswith("_")}


def rebaser(zh, jusqua=None):
    """Copie de l'historique des zones (liste de {date, zones}) ou les
    instantanes anterieurs a chaque harmonisation portent l'ajustement de
    leurs zones. `jusqua` : n'appliquer que les harmonisations de cette date
    ou d'avant (une Lettre ancienne reste telle qu'elle a ete ecrite)."""
    harm = {d: h for d, h in charger().items() if jusqua is None or d <= jusqua}
    if not harm or not zh:
        return zh
    out = copy.deepcopy(zh)
    for h in out:
        for date, x in harm.items():
            if h["date"] >= date:
                continue
            for z in h["zones"]:
                if z.get("province") == x["province"] and z.get("cases") is not None:
                    z["cases"] += x["zones"].get(z.get("name"), 0)
    return out


def deces_entre(avant, apres):
    """Les deces entres par harmonisation entre deux dates (avant exclu,
    apres inclus) : a retrancher d'une moyenne de deces sur la periode."""
    return sum(h.get("deces") or 0 for d, h in charger().items() if avant < d <= apres)


def annulees():
    """Les dates d'harmonisation dont les deces sont repris par une entree
    ulterieure de signe oppose dans la meme province (SitRep 170 : les 314 du
    30 octobre retires le 31). Les deux journees n'ont plus de rattrapage :
    chacune ne porte que ses deces du jour (choix du proprietaire,
    2 novembre 2026)."""
    harm = sorted(charger().items())
    out = set()
    for i, (d, h) in enumerate(harm):
        for d2, h2 in harm[i + 1:]:
            if h2["province"] == h["province"] and (h.get("deces") or 0) + (h2.get("deces") or 0) == 0 \
                    and d not in out and d2 not in out:
                out.update((d, d2))
                break
    return out
