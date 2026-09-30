# -*- coding: utf-8 -*-
"""Mancomunidad de Municipios de la Costa del Sol Occidental - datos de residuos.

Los residuos de Marbella se tratan en el Complejo Ambiental Costa del Sol
(Casares), propiedad de la Mancomunidad y gestionado por Urbaser. Urbaser no
publica datos propios: quien los publica es la Mancomunidad, de dos formas.

1. PDF anual "Datos Residuos AAAA" en
       https://mancomunidad.org/documentacion/residuos-solidos-urbanos/
   Una tabla por fraccion con los doce meses de cada municipio:
     1. Recogida municipal domiciliaria (resto, en toneladas)
     2. Envases ligeros (kg)
     3. Vidrio (kg; desde 2020 separado en iglu y puerta a puerta)
     4-6. Papel-carton (kg; iglu y puerta a puerta)
   Publicados 2014-2020 completos; el de 2021 solo trae enero y febrero. No se
   ha vuelto a publicar ninguno. El colector revisa la pagina en cada pasada
   y si aparece uno nuevo lo incorpora solo.

2. Notas de prensa de balance anual (enero) con el ratio de Marbella en
   kg por habitante y dia. Solo existe para algunos anos y no es mensual.

Trampas del PDF (impreso desde Excel con "Microsoft Print to PDF"):
  - El texto trae numeros partidos ("7.72 7", "10 .172", "24 2.987"). Se
    prueban todas las uniones posibles de tokens y se elige la que hace que
    los meses sumen el total que da la propia tabla. Si ninguna cuadra, la
    fila se descarta en vez de adivinar.
  - Los titulos de las tablas salen desordenados en el texto; las filas de
    Marbella si llegan en el orden de las tablas, y se asignan por el numero
    del titulo ("3.- RECOGIDA SELECTIVA DE VIDRIO").
"""

import html
import io
import json
import os
import re
import time

from .comun import get, ok, aviso

WEB = "https://mancomunidad.org"
PAGINA_DOCS = WEB + "/documentacion/residuos-solidos-urbanos/"
UA_NAV = {"User-Agent": "Mozilla/5.0 (observatorio-residuos; solo lectura)"}
NUMOK = re.compile(r"^(?:0|[1-9]\d{0,2}(?:\.\d{3})*)$")


# ------------------------------------------------------------ PDF anuales

def listar_pdfs():
    """{'2019': 'https://.../3303.pdf'} de los documentos 'Datos residuos AAAA'."""
    h = get(PAGINA_DOCS, headers=UA_NAV).decode("utf-8", "ignore")
    res = {}
    for href, txt in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', h, re.S | re.I):
        t = html.unescape(re.sub(r"<[^>]+>", " ", txt))
        m = re.search(r"datos[\s_]+residuos.*?(20\d\d)", t, re.I)
        if m:
            res[m.group(1)] = href if href.startswith("http") else WEB + href
    return res


def _val(s):
    return int(s.replace(".", ""))


def _fila(tokens, tol):
    """Une tokens hasta obtener numeros validos cuyos meses sumen el total."""
    n = len(tokens)
    if n > 18:
        return None
    mejor = None
    for mask in range(1 << (n - 1)):
        nums, cur, valido = [], tokens[0], True
        for i in range(1, n):
            if mask >> (i - 1) & 1:
                cur += tokens[i]
            else:
                if not NUMOK.match(cur):
                    valido = False
                    break
                nums.append(cur)
                cur = tokens[i]
        if not valido or not NUMOK.match(cur):
            continue
        nums.append(cur)
        if not 2 <= len(nums) <= 13:
            continue
        v = [_val(x) for x in nums]
        if abs(sum(v[:-1]) - v[-1]) <= tol and (mejor is None or len(v) > len(mejor)):
            mejor = v
    return mejor


def _clave(titulo):
    t = titulo.upper()
    if "DOMICILIARIA" in t:
        return "resto"
    if "ENVASES" in t:
        return "envases"
    if "VIDRIO" in t:
        return "vidrio_pap" if "PUERTA" in t else "vidrio"
    if "PAPEL" in t:
        return "papel_pap" if "PUERTA" in t else "papel"
    return None


def interpretar(b, municipio="MARBELLA"):
    """{'resto': [kg por mes], 'envases': [...], ...} y el total comarcal de resto."""
    import pypdf
    r = pypdf.PdfReader(io.BytesIO(b))
    texto = "\n".join((p.extract_text() or "") for p in r.pages)
    titulos = {}
    for l in texto.splitlines():
        m = re.match(r"^\s*(\d+)\s*\.\s*-\s*(.+)$", l.strip())
        if m:
            titulos[int(m.group(1))] = m.group(2).strip()
    orden = [titulos[k] for k in sorted(titulos)]
    filas_mun, filas_tot = [], []
    for l in texto.splitlines():
        s = l.strip()
        up = s.upper()
        if up.startswith(municipio):
            toks = s[len(municipio):].split()
            if toks and all(re.match(r"^[\d.]+$", x) for x in toks):
                filas_mun.append(toks)
        elif re.match(r"^TOTAL\s+\d", up):
            filas_tot.append(s[5:].split())
    res = {}
    for i, toks in enumerate(filas_mun):
        if i >= len(orden):
            break
        clave = _clave(orden[i])
        if not clave:
            continue
        # La tabla de resto va en toneladas redondeadas: la suma admite desfase.
        tol = 13 if clave == "resto" else 2
        v = _fila(toks, tol)
        if v is None:
            aviso(f"{municipio} {orden[i][:40]}: la fila no cuadra con su total, se descarta")
            continue
        meses = v[:-1]
        res[clave] = [x * 1000 for x in meses] if clave == "resto" else meses
    # Total comarcal de resto (primera fila TOTAL del documento, en toneladas).
    if filas_tot:
        v = _fila(filas_tot[0], 13)
        if v:
            res["resto_comarca"] = [x * 1000 for x in v[:-1]]
    return res


def recoger_pdfs(ruta_cache):
    cache = json.load(open(ruta_cache, encoding="utf-8")) if os.path.exists(ruta_cache) else {}
    fallos = []
    try:
        pdfs = listar_pdfs()
    except Exception as e:                                        # noqa: BLE001
        return cache, [f"Mancomunidad listado: {e}"]
    cambios = 0
    for anio, url in sorted(pdfs.items()):
        if anio in cache and cache[anio].get("url") == url:
            continue
        try:
            d = interpretar(get(url, headers=UA_NAV, timeout=120))
            if "resto" not in d:
                raise ValueError("sin tabla de recogida domiciliaria")
            d["url"] = url
            cache[anio] = d
            cambios += 1
            ok(f"Mancomunidad {anio}: {len(d['resto'])} meses, {sum(d['resto']) / 1000:,.0f} t de resto")
        except Exception as e:                                    # noqa: BLE001
            fallos.append(f"Mancomunidad {anio}: {e}")
            aviso(f"{anio}: {e}")
        time.sleep(0.5)
    if cambios:
        with open(ruta_cache, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(cache.items())), f, ensure_ascii=False)
    ok(f"Mancomunidad: {len(cache)} anos en cache ({cambios} nuevos)")
    return cache, fallos


# ------------------------------------------------------- Notas de prensa

BUSQUEDAS = ["kilos+por+habitante", "residuos+urbanos+toneladas", "balance+residuos", "habitante+al+d%C3%ADa", "residuos+urbanos"]
# "Marbella ... con 2,09 kilos por habitante al dia" o "... y Marbella con 1,67 kilos."
PATRON = re.compile(r"Marbella[^.]{0,80}?(\d+,\d+)\s*kilos", re.I)


def recoger_prensa(ruta_cache):
    """Ratio anual de Marbella (kg/hab/dia) de las notas de balance de enero.
    Se acumula en cache: una nota ya leida no se vuelve a pedir."""
    cache = json.load(open(ruta_cache, encoding="utf-8")) if os.path.exists(ruta_cache) else {}
    vistas = set(v["url"] for v in cache.values())
    urls = set()
    for q in BUSQUEDAS:
        try:
            h = get(f"{WEB}/?s={q}", headers=UA_NAV).decode("utf-8", "ignore")
        except Exception:                                         # noqa: BLE001
            continue
        urls |= set(re.findall(r'href="(https://mancomunidad\.org/[a-z0-9-]+/)"', h))
        time.sleep(0.4)
    nuevos = 0
    for u in sorted(urls - vistas):
        if not re.search(r"residuos|rsu|toneladas", u):
            continue
        try:
            h = get(u, headers=UA_NAV).decode("utf-8", "ignore")
        except Exception:                                         # noqa: BLE001
            continue
        fecha = re.search(r'"datePublished":"(\d{4})-(\d{2})', h)
        cuerpo = html.unescape(re.sub(r"<[^>]+>", "", " ".join(re.findall(r"<p[^>]*>(.*?)</p>", h, re.S))))
        m = PATRON.search(cuerpo)
        if fecha and m and "por habitante" in cuerpo and int(fecha.group(2)) <= 3:      # balances de enero-marzo = ano anterior
            anio = str(int(fecha.group(1)) - 1)
            cache[anio] = {"kg_hab_dia": float(m.group(1).replace(",", ".")), "url": u}
            nuevos += 1
            ok(f"Prensa {anio}: Marbella {m.group(1)} kg/hab/dia")
        time.sleep(0.4)
    if nuevos:
        with open(ruta_cache, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(cache.items())), f, ensure_ascii=False, indent=1)
    return cache
