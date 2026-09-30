/* ============================================================================
   app.js — Observatorio de Residuos de Marbella.
   Datos: data/data.js, que escribe pipeline/build_data.py. assets/ no se toca.
   ========================================================================== */
(function () {
  'use strict';

  var D = window.DATOS || {};
  var F = Obs.fmt;
  var M = D.mensual || { x: [] };
  var A = D.anual || { x: [], completo: [] };
  var P = D.poblacion || { x: [] };
  var PA = D.poblacion_anual || { x: [], notas: {} };
  var J = D.junta || { x: [] };
  var PR = D.prensa || { x: [] };
  var PAD = D.padron || { x: [], v: [] };

  /* ------------------------------------------------------------- Fuentes */

  var F_MANC = { txt: 'Mancomunidad de Municipios de la Costa del Sol Occidental · Datos de residuos', url: 'https://mancomunidad.org/documentacion/residuos-solidos-urbanos/' };
  var F_INE = { txt: 'INE · Padrón municipal (Marbella)', url: 'https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177011&idp=1254734710990' };
  var F_JUNTA = { txt: 'Junta de Andalucía · Producción de residuos municipales', url: 'https://www.juntadeandalucia.es/medioambiente/portal/acceso-rediam/estadisticas/estadisticas-oficiales/produccion-gestion-residuos-municipales-andalucia' };
  var F_CALC = { txt: 'Mancomunidad · INE · Junta de Andalucía', url: 'https://mancomunidad.org/documentacion/residuos-solidos-urbanos/' };

  var CH_MES = { txt: 'Mensual' };
  var CH_ANUAL = { txt: 'Anual' };
  var CH_EST = { txt: 'Estimación' };

  /* ------------------------------------------------------------ Utilidades */

  var MES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  var pctF = function (v) { return F.pct(v, 1); };
  var tF = function (v) { return F.num(v) + ' t'; };
  /* Años completos: los únicos que se comparan entre sí. */
  var completos = A.x.filter(function (_, i) { return A.completo[i]; });
  var ia = function (y) { return A.x.indexOf(y); };
  var ultAnio = completos[completos.length - 1];
  var penAnio = completos[completos.length - 2];
  var deAnio = function (k, y) { var i = ia(y); return i < 0 ? null : A[k][i]; };
  var varPct = function (k, y, y0) { var a = deAnio(k, y), b = deAnio(k, y0); return a != null && b ? (a - b) / b * 100 : null; };
  var soloCompletos = function (k) { return completos.map(function (y) { return deAnio(k, y); }); };
  var padronDe = function (y) { var i = PAD.x.indexOf(y); return i < 0 ? null : PAD.v[i]; };
  var mesesDe = function (arr, y) {
    return MES_CORTO.map(function (_, m) { var i = M.x.indexOf(y + '-' + (m < 9 ? '0' : '') + (m + 1)); return i < 0 ? null : arr[i]; });
  };
  var aniosMes = (function () { var s = {}; M.x.forEach(function (p) { s[p.slice(0, 4)] = 1; }); return Object.keys(s).sort().reverse(); })();
  var ultMes = M.x[M.x.length - 1];

  var AVISO_SERIE = 'La Mancomunidad publicó el detalle mensual por municipio de 2014 a 2020; el documento de 2021 solo trae enero y febrero y no ha vuelto a publicar ninguno. ' +
    'El proceso automático revisa su web cada semana: si publica un año nuevo, entra solo.';

  /* ------------------------------------------------------------- Secciones */

  var SECCIONES = [

    /* ================================================= 1. Evolución ====== */
    {
      id: 'evolucion', nombre: 'Evolución',
      titulo: 'Residuos recogidos en Marbella',
      desc: 'Toneladas recogidas en Marbella por fracción y tratadas en el Complejo Ambiental Costa del Sol (Casares), que gestiona Urbaser por encargo de la Mancomunidad. ' +
        'Resto es la bolsa de basura mezclada del contenedor verde oscuro; la recogida selectiva suma envases, vidrio y papel-cartón.',
      render: function () {
        return {
          nota: AVISO_SERIE, notaTipo: 'warn',
          hero: {
            valor: deAnio('total', ultAnio), label: 'Toneladas de residuos recogidas en ' + ultAnio, formato: tF,
            extra: [
              { label: 'Recogida selectiva', valor: deAnio('pct_selectiva', ultAnio), formato: pctF },
              { label: 'Kg por habitante y día', valor: deAnio('kg_hab_dia', ultAnio), formato: function (v) { return F.num(v, 2); } },
              { label: 'Sobre 2019 (prepandemia)', valor: varPct('total', ultAnio, '2019'), formato: function (v) { return F.signo(v) + ' %'; } }
            ]
          },
          kpis: [
            { label: 'Resto · ' + ultAnio, valor: deAnio('resto', ultAnio), unidad: 't', delta: varPct('resto', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, invertir: true, serie: soloCompletos('resto') },
            { label: 'Envases · ' + ultAnio, valor: deAnio('envases', ultAnio), unidad: 't', delta: varPct('envases', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, serie: soloCompletos('envases') },
            { label: 'Vidrio · ' + ultAnio, valor: deAnio('vidrio', ultAnio), unidad: 't', delta: varPct('vidrio', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, serie: soloCompletos('vidrio') },
            { label: 'Papel-cartón · ' + ultAnio, valor: deAnio('papel', ultAnio), unidad: 't', delta: varPct('papel', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, serie: soloCompletos('papel') }
          ],
          cards: [
            {
              titulo: 'Toneladas por fracción', sub: 'Años completos',
              chips: [CH_ANUAL], fuente: F_MANC, ancho: 'full',
              spec: {
                type: 'stack', xType: 'anual', x: completos, yFormat: 'num', unidad: 't',
                series: [
                  { name: 'Resto', data: soloCompletos('resto') },
                  { name: 'Envases', data: soloCompletos('envases') },
                  { name: 'Vidrio', data: soloCompletos('vidrio') },
                  { name: 'Papel-cartón', data: soloCompletos('papel') }
                ]
              }
            },
            {
              titulo: 'Fracción recogida de forma selectiva', sub: 'Envases, vidrio y papel-cartón sobre el total',
              chips: [CH_ANUAL], fuente: F_MANC,
              nota: 'Mide lo que se separa en origen, no lo que acaba reciclado: parte de la selectiva son impropios y parte del resto se recupera en planta.',
              spec: { type: 'bar', xType: 'anual', x: completos, yFormat: 'pct', series: [{ name: '% selectiva', data: soloCompletos('pct_selectiva') }] }
            },
            {
              titulo: 'Recogida selectiva por fracción', sub: 'Toneladas al año',
              chips: [CH_ANUAL], fuente: F_MANC,
              spec: {
                type: 'line', xType: 'anual', x: completos, yFormat: 'num', desdeCero: true,
                series: [
                  { name: 'Envases', data: soloCompletos('envases') },
                  { name: 'Vidrio', data: soloCompletos('vidrio') },
                  { name: 'Papel-cartón', data: soloCompletos('papel') }
                ]
              }
            },
            {
              titulo: 'Kilos por habitante y día', sub: 'Marbella frente a la media andaluza de la Junta',
              chips: [CH_ANUAL], fuente: F_CALC, ancho: 'full',
              nota: 'Marbella: residuos recogidos entre la población empadronada. La diferencia con Andalucía es, sobre todo, la población no empadronada (turistas, segundas residencias). ' +
                'Los puntos de 2023 y 2025 salen de las notas de balance de la Mancomunidad y parecen referirse solo a la fracción resto.',
              spec: (function () {
                var xs = {};
                completos.forEach(function (y) { xs[y] = 1; }); J.x.forEach(function (y) { xs[y] = 1; }); PR.x.forEach(function (y) { xs[y] = 1; });
                var x = Object.keys(xs).sort().filter(function (y) { return y >= (completos[0] || '2014'); });
                var de = function (arrX, arrV) { return x.map(function (y) { var i = arrX.indexOf(y); return i < 0 ? null : arrV[i]; }); };
                return {
                  type: 'line', xType: 'anual', x: x, yFormat: 'dec2', desdeCero: true,
                  series: [
                    { name: 'Marbella, total', data: de(A.x, A.kg_hab_dia) },
                    { name: 'Marbella, solo resto', data: de(A.x, A.kg_hab_dia_resto) },
                    { name: 'Andalucía (Junta)', data: de(J.x, J.kg_hab_dia) },
                    { name: 'Marbella, nota de prensa', data: de(PR.x, PR.kg_hab_dia) }
                  ]
                };
              })()
            }
          ]
        };
      }
    },

    /* ================================================== 2. Mensual ====== */
    {
      id: 'mensual', nombre: 'Mes a mes',
      titulo: 'Estacionalidad de los residuos',
      desc: 'Toneladas de cada mes. En Marbella el verano dispara la basura: es la huella de la población que no figura en el padrón.',
      render: function () {
        var porFraccion = function (y) {
          return {
            type: 'stack', xType: 'cat', x: MES_CORTO, yFormat: 'num', xTodas: true, unidad: 't',
            series: [
              { name: 'Resto', data: mesesDe(M.resto, y) },
              { name: 'Envases', data: mesesDe(M.envases, y) },
              { name: 'Vidrio', data: mesesDe(M.vidrio, y) },
              { name: 'Papel-cartón', data: mesesDe(M.papel, y) }
            ]
          };
        };
        var comparaAnios = function (k) {
          return function (y) {
            var y0 = String(+y - 1);
            return { type: 'line', xType: 'cat', x: MES_CORTO, yFormat: 'num', xTodas: true,
                     series: (aniosMes.indexOf(y0) >= 0 ? [{ name: y0, data: mesesDe(M[k], y0) }] : []).concat([{ name: y, data: mesesDe(M[k], y) }]) };
          };
        };
        var resto = comparaAnios('resto');
        var opcAnios = aniosMes.map(function (y) { return { v: y, txt: y + (y === ultMes.slice(0, 4) && ultMes.slice(5) !== '12' ? ' (ene-' + MES_CORTO[+ultMes.slice(5) - 1] + ')' : '') }; });
        var ref = completos[completos.length - 1];
        var mx = Math.max.apply(null, mesesDe(M.total, ref).filter(function (v) { return v != null; }));
        var mn = Math.min.apply(null, mesesDe(M.total, ref).filter(function (v) { return v != null; }));
        return {
          nota: AVISO_SERIE, notaTipo: 'warn',
          kpis: [
            { label: 'Mes de más residuos · ' + ref, valor: mx, unidad: 't' },
            { label: 'Mes de menos residuos · ' + ref, valor: mn, unidad: 't' },
            { label: 'Pico sobre valle · ' + ref, valor: mn ? (mx / mn - 1) * 100 : null, unidad: '%', dec: 0 },
            { label: 'Peso de Marbella en el resto comarcal · ' + ref, valor: (function () { var i = ia(ref); var s = 0, c = 0; M.x.forEach(function (p, j) { if (p.slice(0, 4) === ref) { s += M.resto[j] || 0; c += M.resto_comarca[j] || 0; } }); return c ? s / c * 100 : null; })(), unidad: '%', dec: 1 }
          ],
          cards: [
            {
              titulo: 'Residuos por mes y fracción', sub: 'Toneladas',
              chips: [CH_MES], fuente: F_MANC, ancho: 'full',
              control: { label: 'Año', valor: ref, opciones: opcAnios, spec: porFraccion },
              spec: porFraccion(ref)
            },
            {
              titulo: 'Resto: un año frente al anterior', sub: 'Toneladas de la fracción resto',
              chips: [CH_MES], fuente: F_MANC,
              control: { label: 'Año', valor: ref, opciones: opcAnios, spec: resto },
              spec: resto(ref)
            },
            {
              titulo: 'Recogida selectiva cada mes', sub: 'Porcentaje sobre el total recogido',
              chips: [CH_MES], fuente: F_MANC,
              spec: { type: 'line', xType: 'mes', x: M.x, yFormat: 'pct', series: [{ name: '% selectiva', data: M.pct_selectiva }] }
            },
            {
              titulo: 'Serie mensual completa', sub: 'Toneladas de resto y de recogida selectiva',
              chips: [CH_MES], fuente: F_MANC, ancho: 'full',
              spec: { type: 'line', xType: 'mes', x: M.x, yFormat: 'num', zoom: true,
                      series: [{ name: 'Resto', data: M.resto }, { name: 'Selectiva', data: M.selectiva }] }
            },
            {
              titulo: 'Peso de Marbella en la Costa del Sol', sub: 'Resto de Marbella sobre el de los 11 municipios y particulares',
              chips: [CH_MES], fuente: F_MANC,
              spec: { type: 'line', xType: 'mes', x: M.x, yFormat: 'pct', series: [{ name: '% del total comarcal', data: M.pct_comarca }] }
            }
          ]
        };
      }
    },

    /* ============================================ 3. Población flotante == */
    {
      id: 'poblacion', nombre: 'Población flotante',
      titulo: 'Cuánta gente vive de verdad en Marbella',
      desc: 'Si cada persona genera lo que un andaluz medio según la Junta de Andalucía, los residuos de Marbella equivalen a una población mayor que la empadronada. ' +
        'Población equivalente = residuos recogidos ÷ kilos por habitante de Andalucía. Población flotante = equivalente − padrón del INE.',
      render: function () {
        var i19 = PA.x.indexOf('2019');
        var iU = PA.x.indexOf(ultAnio);
        var pic = function (y) {
          var v = mesesDe(P.flotante, y).filter(function (x) { return x != null; });
          return v.length ? Math.max.apply(null, v) : null;
        };
        var mesPico = function (y) {
          var v = mesesDe(P.flotante, y), m = -1, mx = -Infinity;
          v.forEach(function (x, k) { if (x != null && x > mx) { mx = x; m = k; } });
          return m >= 0 ? MES_CORTO[m] : '—';
        };
        var perfil = function (y) {
          return { type: 'bar', xType: 'cat', x: MES_CORTO, yFormat: 'num', xTodas: true,
                   series: [{ name: 'Población flotante ' + y, data: mesesDe(P.flotante, y) }] };
        };
        var opc = completos.slice().reverse().map(function (y) { return { v: y, txt: y }; });
        var notas = Object.keys(PA.notas || {}).map(function (k) { return PA.notas[k]; });
        return {
          nota: '<b>Es una estimación, no un censo.</b> Supone que visitantes y residentes no empadronados generan lo mismo que un andaluz medio. ' +
            'Sobrestima si parte de la basura es de hoteles, restaurantes y comercios por encima de la media andaluza; subestima si esos residuos van por gestores privados. ' +
            'El ratio de la Junta cambió de método en 2020 (de unos 490 a unos 550 kg por habitante y año), lo que rebaja la cifra de ese año. ' +
            (notas.length ? 'Nota: ' + notas.join('; ') + '.' : ''),
          notaTipo: 'warn',
          hero: {
            valor: i19 >= 0 ? PA.flotante[i19] : null, label: 'Población flotante media en 2019, último año prepandemia',
            extra: [
              { label: 'Padrón 2019', valor: i19 >= 0 ? PA.padron[i19] : null },
              { label: 'Población equivalente 2019', valor: i19 >= 0 ? PA.equivalente[i19] : null },
              { label: 'Pico mensual 2019 (' + mesPico('2019') + ')', valor: pic('2019') },
              { label: 'Padrón ' + (PAD.x[PAD.x.length - 1] || ''), valor: PAD.v[PAD.v.length - 1] }
            ]
          },
          cards: [
            {
              titulo: 'Población equivalente frente a padrón', sub: 'Personas, cada mes',
              chips: [CH_MES, CH_EST], fuente: F_CALC, ancho: 'full',
              spec: { type: 'line', xType: 'mes', x: P.x, yFormat: 'num', desdeCero: true,
                      series: [{ name: 'Población equivalente por residuos', data: P.equivalente }, { name: 'Padrón INE', data: P.padron }] }
            },
            {
              titulo: 'Población flotante por meses', sub: 'Equivalente menos empadronados',
              chips: [CH_MES, CH_EST], fuente: F_CALC,
              control: { label: 'Año', valor: completos.indexOf('2019') >= 0 ? '2019' : ultAnio, opciones: opc, spec: perfil },
              spec: perfil(completos.indexOf('2019') >= 0 ? '2019' : ultAnio)
            },
            {
              titulo: 'Población flotante media anual', sub: 'Personas por encima del padrón',
              chips: [CH_ANUAL, CH_EST], fuente: F_CALC,
              spec: { type: 'bar', xType: 'anual', x: completos, yFormat: 'num',
                      series: [{ name: 'Población flotante', data: completos.map(function (y) { return PA.flotante[PA.x.indexOf(y)]; }) }] }
            },
            {
              titulo: 'Padrón y población equivalente', sub: 'Media anual',
              chips: [CH_ANUAL, CH_EST], fuente: F_CALC,
              spec: { type: 'bar', xType: 'anual', x: completos, yFormat: 'num',
                      series: [{ name: 'Padrón INE', data: completos.map(function (y) { return PA.padron[PA.x.indexOf(y)]; }) },
                               { name: 'Equivalente por residuos', data: completos.map(function (y) { return PA.equivalente[PA.x.indexOf(y)]; }) }] }
            },
            {
              titulo: 'Ratio de referencia de la Junta', sub: 'Residuos municipales por habitante y año en Andalucía',
              chips: [CH_ANUAL], fuente: F_JUNTA,
              nota: 'Cada cifra procede de la ficha o del informe de la Junta que se cita en la tabla. 2019 no se publicó: se usa la de 2018.',
              spec: { type: 'bar', xType: 'anual', x: J.x, yFormat: 'num', unidad: 'kg',
                      series: [{ name: 'kg por habitante y año', data: J.kg_hab_anio }] }
            },
            {
              titulo: 'Padrón de Marbella', sub: 'Población empadronada a 1 de enero',
              chips: [CH_ANUAL, { txt: 'En vivo', tipo: 'live' }], fuente: F_INE,
              spec: { type: 'line', xType: 'anual', x: PAD.x, yFormat: 'num', series: [{ name: 'Habitantes', data: PAD.v }] }
            }
          ]
        };
      }
    }
  ];

  /* ------------------------------------------------------------- Arranque */

  var ICONO = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M5 6l1 14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-14"/><path d="M10 11v6M14 11v6"/></svg>';

  Obs.init({
    titulo: 'Observatorio de Residuos · Marbella',
    subtitulo: 'Recogida por fracción, reciclaje y población flotante estimada · fuentes oficiales, actualización automática',
    icono: ICONO,
    secciones: SECCIONES,
    actualizado: (D.meta || {}).actualizado,
    fuentes: [F_MANC, F_INE, F_JUNTA],
    metodologia: 'Un proceso automático (<code>pipeline/build_data.py</code>) revisa cada semana la web de la Mancomunidad (PDF anuales y notas de balance), ' +
      'descarga el padrón del INE y recalcula la población equivalente con el ratio andaluz de la Junta de Andalucía. ' +
      'Los números de los PDF se validan comprobando que los doce meses sumen el total que da la propia tabla.',
    pie: 'Los datos son de la Mancomunidad de Municipios de la Costa del Sol Occidental (Complejo Ambiental Costa del Sol, gestionado por Urbaser), el INE y la Junta de Andalucía. ' +
      'La población flotante es una estimación de este observatorio, no una cifra oficial.'
  });

  Obs.estado('Residuos hasta ' + Obs.periodo(ultMes, 'mes') + ' · Padrón ' + ((D.meta || {}).ultimo_padron || '—'), 'live');

})();
