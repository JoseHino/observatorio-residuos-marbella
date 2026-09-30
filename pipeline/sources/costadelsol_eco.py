# -*- coding: utf-8 -*-
"""costadelsol.eco - portal ambiental del Complejo Ambiental Costa del Sol
(Mancomunidad + Urbaser). Pagina de Marbella: https://costadelsol.eco/marbella/

Dos cosas utiles:

1. "Descargar informe historico": PDF (Word) con, por ano, el censo, los doce
   meses y el total de residuos urbanos (t), envases ligeros (kg), papel y
   carton (kg) y vidrio (kg). Cubre 2020 a 2025. La URL cambia cada ano
   (wp-content/uploads/AAAA/MM/AAAA-Marbella.pdf), asi que se lee el enlace de
   la pagina en cada pasada.

2. Bloque del trimestre en curso ("Datos de recogida del segundo trimestre de
   2026: 26.692 t. de R.U., 1.497.136 kg de EE.LL. ..."). Solo muestra el
   ultimo trimestre: se guarda en cache para no perder los anteriores.

Trampas del PDF: los miles vienen a veces con coma ("256,896") y hay espacios
dobles. La ultima columna es el ratio con coma decimal. Las filas se validan
haciendo que los meses sumen el total de la propia tabla.
"""

import html
import io
import json
import os
import re

from .comun import get, ok, aviso
from .mancomunidad import _fila

PAGINA = "https://costadelsol.eco/marbella/"
UA_NAV = {"User-Agent": "Mozilla/5.0 (observatorio-residuos; solo lectura)"}
TRIM = {"primer": 1, "segundo": 2, "tercer": 3, "cuarto": 4}


def _texto(h):
    h = re.sub(r"<(script|style).*?</\1>", "", h, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)))


def _num(s):
    return int(s.replace(".", "").replace(",", ""))


def interpretar_pdf(b):
    import pypdf
    r = pypdf.PdfReader(io.BytesIO(b))
    tabla, res = None, {}
    for pg in r.pages:
        for l in (pg.extract_text() or "").splitlines():
            s = l.strip()
            low = s.lower()
            if low.startswith("residuos urbanos"):
                tabla = "resto"
            elif low.startswith("envases"):
                tabla = "envases"
            elif low.startswith("papel"):
                tabla = "papel"
            elif low.startswith("vidrio"):
                tabla = "vidrio"
            m = re.match(r"^(20\d\d)\s+(.+)$", s)
            if not (m and tabla):
                continue
            toks = m.group(2).split()
            if len(toks) < 4:
                continue
            ratio = toks[-1]
            censo = _num(toks[0])
            medio = [t.replace(",", ".") for t in toks[1:-1]]
            v = _fila(medio, 12 if tabla == "resto" else 2)
            if v is None and len(medio) == 13 and all(re.match(r"^\d{1,3}(\.\d{3})*$", x) for x in medio):
                # Errata de la fuente: los meses no suman exactamente el total.
                # Se aceptan si la diferencia es menor del 0,5 % y se avisa.
                cand = [int(x.replace(".", "")) for x in medio]
                if cand[-1] and abs(sum(cand[:12]) - cand[-1]) / cand[-1] < 0.005:
                    aviso(f"costadelsol.eco {tabla} {m.group(1)}: los meses suman {sum(cand[:12]):,} y el total dice {cand[-1]:,}; se usan los meses")
                    v = cand
            if v is None or len(v) != 13:
                aviso(f"costadelsol.eco {tabla} {m.group(1)}: la fila no cuadra, se descarta")
                continue
            d = res.setdefault(m.group(1), {"censo": censo})
            # resto viene en toneladas; el resto de fracciones en kg
            d[tabla] = [x * 1000 for x in v[:12]] if tabla == "resto" else v[:12]
            if tabla == "resto":
                d["kg_hab_dia"] = float(ratio.replace(",", "."))
    return res


def recoger(ruta_cache):
    cache = json.load(open(ruta_cache, encoding="utf-8")) if os.path.exists(ruta_cache) else {"anios": {}, "trimestres": {}}
    fallos = []
    h = get(PAGINA, headers=UA_NAV).decode("utf-8", "ignore")

    # --- Informe historico -------------------------------------------------
    m = re.search(r'href="([^"]+\.pdf)"[^>]*>\s*(?:<[^>]+>\s*)*Descargar informe hist', h, re.I)
    if m:
        url = m.group(1)
        if cache.get("url") != url:
            try:
                anios = interpretar_pdf(get(url, headers=UA_NAV))
                completos = {a: d for a, d in anios.items() if all(k in d for k in ("resto", "envases", "papel", "vidrio"))}
                if not completos:
                    raise ValueError("el informe no trae tablas completas")
                cache["anios"].update(completos)
                cache["url"] = url
                ok(f"costadelsol.eco: informe {url.rsplit('/', 1)[-1]}, anos {', '.join(sorted(completos))}")
            except Exception as e:                                # noqa: BLE001
                fallos.append(f"costadelsol.eco informe: {e}")
                aviso(str(e))
        else:
            ok(f"costadelsol.eco: informe sin cambios ({url.rsplit('/', 1)[-1]})")
    else:
        fallos.append("costadelsol.eco: no se encuentra el enlace del informe historico")

    # --- Trimestre en curso -----------------------------------------------
    t = _texto(h)
    mt = re.search(r"Datos de recogida del (\w+) trimestre de (20\d\d)\s+([\d.]+) t\. de R\.U\..*?"
                   r"([\d.]+) kg de EE\.LL\..*?([\d.]+) kg de P/C.*?([\d.]+) kg de Vidrio", t, re.S)
    if mt and mt.group(1).lower() in TRIM:
        clave = f"{mt.group(2)}T{TRIM[mt.group(1).lower()]}"
        cache["trimestres"][clave] = {"resto_t": _num(mt.group(3)), "envases_kg": _num(mt.group(4)),
                                      "papel_kg": _num(mt.group(5)), "vidrio_kg": _num(mt.group(6))}
        ok(f"costadelsol.eco: {clave} {mt.group(3)} t de resto")
    else:
        aviso("costadelsol.eco: no se encuentra el bloque del trimestre")

    with open(ruta_cache, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, sort_keys=True)
    return cache, fallos
