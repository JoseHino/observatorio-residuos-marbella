# -*- coding: utf-8 -*-
"""Junta de Andalucia - Informe de Medio Ambiente en Andalucia (IMA).

La pagina "IMA de un vistazo" de cada edicion enlaza una hoja de calculo (ODS)
con la serie completa "Generacion de residuos de competencia local" en
Andalucia, kg por habitante y ano:

    https://www.juntadeandalucia.es/medioambiente/portal/acceso-rediam/informe-medio-ambiente/ima-AAAA-vistazo
    -> /medioambiente/portal/documents/d/global/10-01-residuos-municipales-por-habitante-ima-AAAA

La Junta ha revisado cifras antiguas (p. ej. 2017 figuraba con 476 kg en la
ficha RE01 de 2018 y con 516,6 kg en la edicion 2025), asi que se usa siempre
la serie completa de la edicion mas reciente, nunca se mezclan ediciones.

La edicion AAAA trae el dato de AAAA-1. El colector prueba de la edicion del
ano siguiente hacia atras y se queda con la primera que exista: cuando la
Junta publique una nueva, entra sola.

El ODS se lee con la biblioteca estandar (zip + XML), sin dependencias.
"""

import io
import re
import xml.etree.ElementTree as ET
import zipfile

from .comun import get, ok

BASE = "https://www.juntadeandalucia.es"
VISTAZO = BASE + "/medioambiente/portal/acceso-rediam/informe-medio-ambiente/ima-{}-vistazo"
UA_NAV = {"User-Agent": "Mozilla/5.0 (observatorio-residuos; solo lectura)"}
T = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
X = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
O = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"


def _filas_ods(b):
    root = ET.fromstring(zipfile.ZipFile(io.BytesIO(b)).read("content.xml"))
    filas = []
    for r in root.iter(f"{{{T}}}table-row"):
        fila = []
        for c in r:
            if not c.tag.endswith("table-cell"):
                continue
            rep = min(int(c.get(f"{{{T}}}number-columns-repeated", "1")), 20)
            v = c.get(f"{{{O}}}value")
            if v is None:
                v = " ".join("".join(p.itertext()) for p in c.iter(f"{{{X}}}p")) or None
            fila += [v] * rep
        filas.append(fila)
    return filas


def serie_andalucia(anio_actual):
    """{'x': ['2006', ...], 'v': [kg/hab/ano], 'edicion': 2025, 'url': ...}"""
    for ed in range(anio_actual + 1, 2023, -1):
        try:
            h = get(VISTAZO.format(ed), headers=UA_NAV, reintentos=1).decode("utf-8", "ignore")
        except Exception:                                         # noqa: BLE001
            continue
        m = re.search(r'href="([^"]*residuos-municipales-por-habitante[^"]*)"', h)
        if not m:
            continue
        url = m.group(1) if m.group(1).startswith("http") else BASE + m.group(1)
        filas = _filas_ods(get(url, headers=UA_NAV))
        serie = {}
        for f in filas:
            if len(f) >= 2 and f[0] and re.fullmatch(r"(19|20)\d\d", f[0].strip()):
                try:
                    serie[f[0].strip()] = round(float(f[1]), 1)
                except (TypeError, ValueError):
                    pass
        if serie:
            xs = sorted(serie)
            ok(f"Junta: edicion IMA {ed}, serie {xs[0]}-{xs[-1]}, {xs[-1]}: {serie[xs[-1]]} kg/hab")
            return {"x": xs, "v": [serie[a] for a in xs], "edicion": ed,
                    "url": url, "pagina": VISTAZO.format(ed)}
    raise RuntimeError("no se encuentra ninguna edicion del IMA con la serie de residuos")
