# -*- coding: utf-8 -*-
"""Colector del Observatorio de Residuos de Marbella: escribe data/data.js.

    python pipeline/build_data.py

Una sola fuente para los residuos y el censo:
  - costadelsol.eco, portal del Complejo Ambiental Costa del Sol (Mancomunidad
    de la Costa del Sol Occidental + Urbaser): informe historico de Marbella
    (meses por fraccion y censo de cada ano) y bloque del trimestre en curso.

Una sola referencia externa, solo para la poblacion flotante:
  - Junta de Andalucia, Informe de Medio Ambiente: kg de residuos de
    competencia local por habitante y ano en Andalucia (serie completa de la
    ultima edicion).

Poblacion equivalente = residuos de Marbella / ratio andaluz por habitante.
Poblacion flotante estimada = poblacion equivalente - censo.

Reglas del kit: solo GET; un fallo de fuente conserva lo publicado; nunca se
escribe un data.js con menos del 90 % de los valores vigentes.
"""

import calendar
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import costadelsol_eco, junta                 # noqa: E402
from sources.comun import escribir_js, paso, ok, aviso      # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "data", "data.js")
CACHE_ECO = os.path.join(RAIZ, "pipeline", "cache", "costadelsol_eco.json")
FRACCIONES = ["resto", "envases", "vidrio", "papel"]


def _vigente():
    if not os.path.exists(SALIDA):
        return None
    try:
        txt = open(SALIDA, encoding="utf-8").read()
        m = re.search(r"window\.\w+\s*=\s*(\{.*\});?\s*$", txt, re.S)
        return json.loads(m.group(1)) if m else None
    except Exception:                                             # noqa: BLE001
        return None


def _contar(obj):
    if isinstance(obj, dict):
        return sum(_contar(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(1 if isinstance(v, (int, float)) and not isinstance(v, bool) else _contar(v) for v in obj)
    return 0


def _dias(anio):
    return 366 if calendar.isleap(int(anio)) else 365


def recoger(previo):
    hoy = datetime.date.today()
    datos = {"meta": {"actualizado": datetime.datetime.now(datetime.timezone.utc)
                      .strftime("%Y-%m-%dT%H:%M:%SZ")}}
    fallos = []

    # --- costadelsol.eco ------------------------------------------------------
    paso("costadelsol.eco - informe historico y trimestre en curso")
    try:
        eco, f = costadelsol_eco.recoger(CACHE_ECO)
        fallos += f
    except Exception as e:                                        # noqa: BLE001
        fallos.append(f"costadelsol.eco: {e}")
        aviso(str(e))
        eco = json.load(open(CACHE_ECO, encoding="utf-8")) if os.path.exists(CACHE_ECO) else {"anios": {}, "trimestres": {}}
    anios_eco = eco["anios"]
    datos["fuente_eco"] = eco.get("url")

    # --- Junta ----------------------------------------------------------------
    paso("Junta de Andalucia - residuos de competencia local por habitante")
    try:
        jun = junta.serie_andalucia(hoy.year)
    except Exception as e:                                        # noqa: BLE001
        fallos.append(f"Junta: {e}")
        aviso(str(e))
        jun = (previo or {}).get("junta") or {"x": [], "v": []}
    datos["junta"] = jun
    ratio_de = dict(zip(jun["x"], jun["v"]))

    def ratio(anio):
        """(kg/hab/ano, ano usado). Si el ano aun no esta publicado, el ultimo disponible."""
        if anio in ratio_de:
            return ratio_de[anio], anio
        prev = [a for a in ratio_de if a < anio]
        return (ratio_de[max(prev)], max(prev)) if prev else (None, None)

    # --- Serie mensual --------------------------------------------------------
    t = lambda v: None if v is None else round(v / 1000, 1)       # noqa: E731
    x, mes = [], {k: [] for k in FRACCIONES}
    for anio in sorted(anios_eco):
        d = anios_eco[anio]
        for i in range(12):
            x.append(f"{anio}-{i + 1:02d}")
            for k in FRACCIONES:
                mes[k].append(t(d[k][i]))
    mes["x"] = x
    mes["total"] = [round(sum(mes[k][i] for k in FRACCIONES), 1) for i in range(len(x))]
    mes["selectiva"] = [round(mes["total"][i] - mes["resto"][i], 1) for i in range(len(x))]
    mes["pct_selectiva"] = [round(mes["selectiva"][i] / mes["total"][i] * 100, 1) for i in range(len(x))]
    datos["mensual"] = mes

    # --- Serie anual ----------------------------------------------------------
    anios = sorted(anios_eco)
    an = {"x": anios, "censo": [anios_eco[a]["censo"] for a in anios],
          "kg_hab_dia_resto_fuente": [anios_eco[a].get("kg_hab_dia") for a in anios]}
    for k in FRACCIONES:
        an[k] = [round(sum(anios_eco[a][k]) / 1000, 1) for a in anios]
    an["total"] = [round(sum(an[k][i] for k in FRACCIONES), 1) for i in range(len(anios))]
    an["selectiva"] = [round(an["total"][i] - an["resto"][i], 1) for i in range(len(anios))]
    an["pct_selectiva"] = [round(an["selectiva"][i] / an["total"][i] * 100, 1) for i in range(len(anios))]
    an["kg_hab_dia"] = [round(an["total"][i] * 1000 / an["censo"][i] / _dias(a), 2) for i, a in enumerate(anios)]
    for k in ("envases", "vidrio", "papel"):
        an[f"kg_hab_anio_{k}"] = [round(an[k][i] * 1000 / an["censo"][i], 1) for i in range(len(anios))]
    datos["anual"] = an
    censo_de = dict(zip(anios, an["censo"]))

    # --- Trimestral: meses cerrados + trimestres que solo publica la web --------
    tri = {}
    for i, p in enumerate(x):
        tri.setdefault(f"{p[:4]}T{(int(p[5:]) - 1) // 3 + 1}", []).append(i)
    tx = sorted(tri)
    trim = {"x": tx, "fuente": ["informe"] * len(tx)}
    for k in FRACCIONES:
        trim[k] = [round(sum(mes[k][i] for i in tri[q]), 1) for q in tx]
    for q, v in sorted(eco.get("trimestres", {}).items()):
        if q in tri:
            continue
        # Trimestres que la web ya no muestra y no llegaron a guardarse: hueco
        # explicito (null), para que la grafica no salte de 4T a 2T sin avisar.
        while trim["x"]:
            y, n = int(trim["x"][-1][:4]), int(trim["x"][-1][-1])
            sig = f"{y + (n == 4)}T{1 if n == 4 else n + 1}"
            if sig >= q:
                break
            trim["x"].append(sig)
            trim["fuente"].append("sin dato")
            for k in FRACCIONES:
                trim[k].append(None)
        trim["x"].append(q)
        trim["fuente"].append("web")
        trim["resto"].append(float(v["resto_t"]))
        trim["envases"].append(t(v["envases_kg"]))
        trim["papel"].append(t(v["papel_kg"]))
        trim["vidrio"].append(t(v["vidrio_kg"]))
    trim["total"] = [round(sum(trim[k][i] for k in FRACCIONES), 1) if trim["resto"][i] is not None else None
                     for i in range(len(trim["x"]))]
    datos["trimestral"] = trim

    # --- Poblacion equivalente y flotante ---------------------------------------
    paso("Poblacion equivalente")
    notas = {}
    eq, flo, cen = [], [], []
    for i, p in enumerate(x):
        a = p[:4]
        r, usado = ratio(a)
        if usado and usado != a:
            notas[a] = f"{a}: la Junta aún no ha publicado su dato; se usa el de {usado}"
        dias_mes = calendar.monthrange(int(a), int(p[5:]))[1]
        e = round(mes["total"][i] * 1000 / (r / _dias(a) * dias_mes)) if r else None
        eq.append(e)
        cen.append(censo_de[a])
        flo.append(e - censo_de[a] if e is not None else None)
    datos["poblacion"] = {"x": x, "equivalente": eq, "flotante": flo, "censo": cen}

    pa = {"x": anios, "equivalente": [], "flotante": [], "censo": an["censo"], "ratio": [], "ratio_anio": []}
    for i, a in enumerate(anios):
        r, usado = ratio(a)
        e = round(an["total"][i] * 1000 / r) if r else None
        pa["equivalente"].append(e)
        pa["flotante"].append(e - an["censo"][i] if e is not None else None)
        pa["ratio"].append(r)
        pa["ratio_anio"].append(usado)
        if e is not None:
            ok(f"{a}: equivalente {e:,} - censo {an['censo'][i]:,} = flotante media {e - an['censo'][i]:,}")

    # Trimestres del ano en curso (solo web): censo del ultimo ano publicado.
    pt = {"x": [], "equivalente": [], "flotante": [], "censo_anio": []}
    for i, q in enumerate(trim["x"]):
        if trim["fuente"][i] != "web":
            continue
        a, n = q[:4], int(q[-1])
        r, usado = ratio(a)
        ca = max(censo_de) if censo_de else None
        dias = sum(calendar.monthrange(int(a), m)[1] for m in range(3 * n - 2, 3 * n + 1))
        if r and ca:
            e = round(trim["total"][i] * 1000 / (r / _dias(a) * dias))
            pt["x"].append(q)
            pt["equivalente"].append(e)
            pt["flotante"].append(e - censo_de[ca])
            pt["censo_anio"].append(ca)
            notas[q] = f"{q}: sin censo de {a} todavía; se usa el de {ca}"
            if usado != a:
                notas[a] = f"{a}: la Junta aún no ha publicado su dato; se usa el de {usado}"
    pa["trimestres_web"] = pt
    pa["notas"] = notas
    datos["poblacion_anual"] = pa

    datos["meta"]["ultimo_periodo"] = x[-1] if x else None
    datos["meta"]["ultimo_trimestre"] = trim["x"][-1] if trim["x"] else None
    datos["meta"]["junta_ultimo"] = jun["x"][-1] if jun.get("x") else None
    datos["meta"]["fallos"] = fallos
    return datos, fallos


def main():
    print("== Observatorio de Residuos de Marbella - recoleccion ==")
    previo = _vigente()
    datos, fallos = recoger(previo)
    nuevos = _contar(datos)
    if previo is not None and "junta" in previo and isinstance(previo.get("junta"), dict) and "edicion" in previo["junta"]:
        antes = _contar(previo)
        if antes and nuevos < antes * 0.9:
            aviso(f"ABORTADO: {nuevos} valores frente a {antes} publicados. No se sobrescribe data.js.")
            return 1
    paso("Escritura")
    escribir_js(SALIDA, datos)
    if fallos:
        aviso(f"{len(fallos)} incidencia(s): " + "; ".join(fallos))
    m = datos["meta"]
    print(f"\nListo. {nuevos} valores. Mensual hasta {m['ultimo_periodo']}, trimestral hasta {m['ultimo_trimestre']}, "
          f"Junta hasta {m['junta_ultimo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
