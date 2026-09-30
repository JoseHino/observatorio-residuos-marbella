# -*- coding: utf-8 -*-
"""Colector del Observatorio de Residuos de Marbella: escribe data/data.js.

    python pipeline/build_data.py

Fuentes:
  - costadelsol.eco (portal del Complejo Ambiental Costa del Sol: Mancomunidad
    + Urbaser): informe historico de Marbella 2020-2025 y trimestre en curso.
  - Mancomunidad de Municipios de la Costa del Sol Occidental: PDF anuales con
    la recogida mensual de Marbella por fraccion, 2014-2019 (y 2020-2021, que
    se sustituyen por la cifra revisada de costadelsol.eco).
  - INE, Padron municipal (serie DPOP13669, Marbella, poblacion a 1 de enero).
  - Junta de Andalucia (REDIAM / Informe de Medio Ambiente): kg de residuos
    municipales por habitante y ano en Andalucia. No hay fichero descargable
    estable, asi que la serie va declarada abajo con la fuente de cada cifra.

Poblacion equivalente = residuos de Marbella / (ratio andaluz por habitante).
Poblacion flotante estimada = poblacion equivalente - padron.

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

from sources import ine, mancomunidad, costadelsol_eco   # noqa: E402
from sources.comun import escribir_js, paso, ok, aviso    # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "data", "data.js")
CACHE_PDF = os.path.join(RAIZ, "pipeline", "cache", "mancomunidad.json")
CACHE_ECO = os.path.join(RAIZ, "pipeline", "cache", "costadelsol_eco.json")

SERIE_PADRON = "DPOP13669"          # Marbella. Total. Total habitantes (Padron, 1 de enero)

# Junta de Andalucia: residuos municipales en Andalucia, kg por habitante y ano.
# Cada ficha RE01 describe el ano anterior a su edicion.
_RE01 = "https://www.juntadeandalucia.es/medioambiente/portal/documents/20151/"
_IMA = "https://www.juntadeandalucia.es/medioambiente/portal/acceso-rediam/estadisticas/estadisticas-oficiales/produccion-gestion-residuos-municipales-andalucia"
JUNTA = {
    "2014": (504.0, "Ficha RE01, edición 2015", _RE01 + "393430/RE01_2015.pdf"),
    "2015": (489.0, "Ficha RE01, edición 2016", _RE01 + "386568/RE01_2016.pdf"),
    "2016": (498.0, "Ficha RE01, edición 2017", _RE01 + "411920/RE01_2017.pdf"),
    "2017": (476.0, "Ficha RE01, edición 2018", _RE01 + "393600/RE01_2018.pdf"),
    "2018": (488.3, "Ficha RE01, edición 2019", _RE01 + "24243301/RE01_2019.pdf/f28a2d0e-f00b-d89b-95d5-6c2dc8f3dfa4"),
    "2020": (548.9, "IMA 2023: 570,3 kg en 2021, un 3,9 % más que en 2020 (valor derivado)", _IMA),
    "2021": (570.3, "Informe de Medio Ambiente en Andalucía 2023", _IMA),
    "2022": (555.1, "Informe de Medio Ambiente en Andalucía 2024", _IMA),
    "2023": (519.7, "Informe de Medio Ambiente en Andalucía 2024", _IMA),
}

FRACCIONES = ["resto", "envases", "vidrio", "papel"]     # vidrio y papel suman iglu + puerta a puerta


def ratio_junta(anio):
    """(kg/hab/ano, ano del dato usado, aviso) con el ano mas cercano anterior si falta."""
    if anio in JUNTA:
        return JUNTA[anio][0], anio, None
    previos = [a for a in JUNTA if a < anio]
    if not previos:
        return None, None, None
    a = max(previos)
    return JUNTA[a][0], a, f"{anio} sin dato publicado; se usa el de {a}"


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


def recoger(previo):
    datos = {"meta": {"actualizado": datetime.datetime.now(datetime.timezone.utc)
                      .strftime("%Y-%m-%dT%H:%M:%SZ")}}
    fallos = []

    # --- Padron ---------------------------------------------------------------
    paso("INE - Padron de Marbella")
    pad = ine.anual(SERIE_PADRON)
    if pad["x"]:
        padron = dict(zip(pad["x"], [int(v) for v in pad["v"]]))
        ok(f"padron: {pad['x'][0]}-{pad['x'][-1]}, {pad['x'][-1]}: {padron[pad['x'][-1]]:,}")
    else:
        fallos.append("INE padron")
        padron = dict(zip(previo["padron"]["x"], previo["padron"]["v"])) if previo and "padron" in previo else {}
    datos["padron"] = {"x": sorted(padron), "v": [padron[a] for a in sorted(padron)]}

    # --- Mancomunidad: PDF anuales ------------------------------------------
    paso("Mancomunidad - Datos residuos (PDF anuales)")
    cache, f = mancomunidad.recoger_pdfs(CACHE_PDF)
    fallos += f

    # --- costadelsol.eco: informe historico y trimestre en curso -------------
    paso("costadelsol.eco - informe historico de Marbella")
    try:
        eco, f = costadelsol_eco.recoger(CACHE_ECO)
        fallos += f
    except Exception as e:                                        # noqa: BLE001
        fallos.append(f"costadelsol.eco: {e}")
        aviso(str(e))
        eco = json.load(open(CACHE_ECO, encoding="utf-8")) if os.path.exists(CACHE_ECO) else {"anios": {}, "trimestres": {}}

    # Cada ano sale de UNA fuente: costadelsol.eco (mas reciente y revisada)
    # cuando la tiene; si no, el PDF de la Mancomunidad.
    por_anio, origen = {}, {}
    for anio, d in cache.items():
        n = len(d["resto"])
        suma = lambda a, b: [(d[a][i] if a in d else 0) + (d[b][i] if b in d else 0) for i in range(n)]   # noqa: E731
        por_anio[anio] = {"resto": d["resto"], "envases": d.get("envases"),
                          "vidrio": suma("vidrio", "vidrio_pap") if "vidrio" in d else None,
                          "papel": suma("papel", "papel_pap") if "papel" in d else None,
                          "comarca": d.get("resto_comarca")}
        origen[anio] = "mancomunidad"
    for anio, d in eco["anios"].items():
        por_anio[anio] = {k: d[k] for k in FRACCIONES}
        por_anio[anio]["comarca"] = None
        origen[anio] = "costadelsol.eco"
    datos["origen"] = dict(sorted(origen.items()))

    x, series = [], {k: [] for k in FRACCIONES + ["comarca"]}
    for anio in sorted(por_anio):
        d = por_anio[anio]
        for i in range(len(d["resto"])):
            x.append(f"{anio}-{i + 1:02d}")
            for k in FRACCIONES + ["comarca"]:
                series[k].append(d[k][i] if d.get(k) and i < len(d[k]) else None)
    # kg -> toneladas con un decimal
    t = lambda v: None if v is None else round(v / 1000, 1)   # noqa: E731
    mes = {"x": x}
    for k in FRACCIONES:
        mes[k] = [t(v) for v in series[k]]
    mes["resto_comarca"] = [t(v) for v in series["comarca"]]
    mes["total"] = [round(sum(mes[k][i] for k in FRACCIONES), 1)
                    if all(mes[k][i] is not None for k in FRACCIONES) else None for i in range(len(x))]
    mes["selectiva"] = [round(mes["total"][i] - mes["resto"][i], 1) if mes["total"][i] is not None else None
                        for i in range(len(x))]
    mes["pct_selectiva"] = [round(mes["selectiva"][i] / mes["total"][i] * 100, 1) if mes["total"][i] else None
                            for i in range(len(x))]
    mes["pct_comarca"] = [round(mes["resto"][i] / mes["resto_comarca"][i] * 100, 1)
                          if mes["resto_comarca"][i] else None for i in range(len(x))]
    datos["mensual"] = mes
    datos["fuentes_pdf"] = {a: cache[a]["url"] for a in sorted(cache)}
    datos["fuente_eco"] = eco.get("url")

    # --- Trimestral: meses cerrados + trimestres que solo publica la web ------
    tri = {}
    for i, p in enumerate(x):
        q = f"{p[:4]}T{(int(p[5:]) - 1) // 3 + 1}"
        tri.setdefault(q, []).append(i)
    tx = sorted(q for q, idx in tri.items() if len(idx) == 3)
    trim = {"x": tx, "fuente": ["mensual"] * len(tx)}
    for k in FRACCIONES:
        trim[k] = [round(sum(mes[k][i] or 0 for i in tri[q]), 1) for q in tx]
    for q, v in sorted(eco.get("trimestres", {}).items()):
        if q in trim["x"]:
            continue
        trim["x"].append(q)
        trim["fuente"].append("web")
        trim["resto"].append(v["resto_t"])
        trim["envases"].append(round(v["envases_kg"] / 1000, 1))
        trim["papel"].append(round(v["papel_kg"] / 1000, 1))
        trim["vidrio"].append(round(v["vidrio_kg"] / 1000, 1))
    datos["trimestral"] = trim

    # --- Anual -------------------------------------------------------------
    anios = sorted({p[:4] for p in x})
    anual = {"x": anios, "meses": [], "completo": []}
    for k in FRACCIONES + ["total", "selectiva"]:
        anual[k] = []
    for a in anios:
        idx = [i for i, p in enumerate(x) if p.startswith(a)]
        anual["meses"].append(len(idx))
        anual["completo"].append(len(idx) == 12)
        for k in FRACCIONES + ["total", "selectiva"]:
            anual[k].append(round(sum(mes[k][i] or 0 for i in idx), 1))
    anual["pct_selectiva"] = [round(s / tt * 100, 1) if tt else None for s, tt in zip(anual["selectiva"], anual["total"])]
    anual["padron"] = [padron.get(a) for a in anios]
    anual["kg_hab_dia"] = [
        round(anual["total"][i] * 1000 / anual["padron"][i] / (366 if calendar.isleap(int(a)) else 365), 2)
        if anual["completo"][i] and anual["padron"][i] else None for i, a in enumerate(anios)]
    anual["kg_hab_dia_resto"] = [
        round(anual["resto"][i] * 1000 / anual["padron"][i] / (366 if calendar.isleap(int(a)) else 365), 2)
        if anual["completo"][i] and anual["padron"][i] else None for i, a in enumerate(anios)]
    datos["anual"] = anual

    # --- Poblacion equivalente y flotante -----------------------------------
    paso("Poblacion equivalente (ratio de la Junta)")
    eq, flo, ratio_m, pad_m = [], [], [], []
    for i, p in enumerate(x):
        a = p[:4]
        r, _, _ = ratio_junta(a)
        dias_mes = calendar.monthrange(int(a), int(p[5:]))[1]
        dias_anio = 366 if calendar.isleap(int(a)) else 365
        tot = mes["total"][i]
        if r and tot is not None:
            e = round(tot * 1000 / (r / dias_anio * dias_mes))
            eq.append(e)
            ratio_m.append(round(r / dias_anio, 3))
            pd = padron.get(a)
            pad_m.append(pd)
            flo.append(e - pd if pd else None)
        else:
            eq.append(None); flo.append(None); ratio_m.append(None); pad_m.append(padron.get(a))
    datos["poblacion"] = {"x": x, "equivalente": eq, "flotante": flo, "padron": pad_m, "ratio_dia": ratio_m}
    eqa, floa, notas = [], [], {}
    for i, a in enumerate(anios):
        r, usado, nota = ratio_junta(a)
        if nota:
            notas[a] = nota
        if r and anual["completo"][i]:
            e = round(anual["total"][i] * 1000 / r)
            eqa.append(e)
            floa.append(e - padron[a] if a in padron else None)
        else:
            eqa.append(None); floa.append(None)
    datos["poblacion_anual"] = {"x": anios, "equivalente": eqa, "flotante": floa,
                                "padron": [padron.get(a) for a in anios], "notas": notas}
    datos["junta"] = {"x": sorted(JUNTA), "kg_hab_anio": [JUNTA[a][0] for a in sorted(JUNTA)],
                      "kg_hab_dia": [round(JUNTA[a][0] / 365, 2) for a in sorted(JUNTA)],
                      "fuente": [JUNTA[a][1] for a in sorted(JUNTA)], "url": [JUNTA[a][2] for a in sorted(JUNTA)]}
    for a, e, fl in zip(anios, eqa, floa):
        if e:
            ok(f"{a}: equivalente {e:,} - padron = flotante media {fl:,}")

    datos["meta"]["ultimo_periodo"] = x[-1] if x else None
    datos["meta"]["ultimo_trimestre"] = trim["x"][-1] if trim["x"] else None
    datos["meta"]["ultimo_padron"] = datos["padron"]["x"][-1] if datos["padron"]["x"] else None
    datos["meta"]["fallos"] = fallos
    return datos, fallos


def main():
    print("== Observatorio de Residuos de Marbella - recoleccion ==")
    previo = _vigente()
    datos, fallos = recoger(previo)
    nuevos = _contar(datos)
    if previo is not None:
        antes = _contar(previo)
        if antes and nuevos < antes * 0.9:
            aviso(f"ABORTADO: {nuevos} valores frente a {antes} publicados. No se sobrescribe data.js.")
            return 1
    paso("Escritura")
    escribir_js(SALIDA, datos)
    if fallos:
        aviso(f"{len(fallos)} incidencia(s): " + "; ".join(fallos))
    print(f"\nListo. {nuevos} valores. Ultimo mes: {datos['meta']['ultimo_periodo']}, padron {datos['meta']['ultimo_padron']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
