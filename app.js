/* ============================================================================
   app.js — Observatorio de Residuos de Marbella.
   Residuos y censo: costadelsol.eco. Ratio andaluz: Junta de Andalucía (IMA).
   Datos: data/data.js, que escribe pipeline/build_data.py. assets/ no se toca.
   ========================================================================== */
(function () {
  'use strict';

  var D = window.DATOS || {};
  var F = Obs.fmt;
  var M = D.mensual || { x: [] };
  var A = D.anual || { x: [] };
  var TR = D.trimestral || { x: [], fuente: [] };
  var P = D.poblacion || { x: [] };
  var PA = D.poblacion_anual || { x: [], notas: {}, trimestres_web: { x: [] } };
  var J = D.junta || { x: [], v: [] };

  /* ------------------------------------------------------------- Fuentes */

  var F_ECO = { txt: 'costadelsol.eco · Informe histórico de Marbella', url: 'https://costadelsol.eco/marbella/#histrico' };
  var F_JUNTA = { txt: 'Junta de Andalucía · Informe de Medio Ambiente ' + (J.edicion || ''), url: J.pagina || 'https://www.juntadeandalucia.es/medioambiente/portal/acceso-rediam/informe-medio-ambiente/ima-2025-vistazo' };
  var F_CALC = { txt: 'costadelsol.eco · Junta de Andalucía', url: 'https://costadelsol.eco/marbella/#histrico' };

  var CH_MES = { txt: 'Mensual' };
  var CH_TRIM = { txt: 'Trimestral', tipo: 'live' };
  var CH_ANUAL = { txt: 'Anual' };
  var CH_EST = { txt: 'Estimación' };

  /* ------------------------------------------------------------ Utilidades */

  var MES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  var pctF = function (v) { return F.pct(v, 1); };
  var tF = function (v) { return F.num(v) + ' t'; };
  var ia = function (y) { return A.x.indexOf(y); };
  var ultAnio = A.x[A.x.length - 1];
  var penAnio = A.x[A.x.length - 2];
  var deAnio = function (k, y) { var i = ia(y); return i < 0 ? null : A[k][i]; };
  var varPct = function (k, y, y0) { var a = deAnio(k, y), b = deAnio(k, y0); return a != null && b ? (a - b) / b * 100 : null; };
  var mesesDe = function (arr, y) {
    return MES_CORTO.map(function (_, m) { var i = M.x.indexOf(y + '-' + (m < 9 ? '0' : '') + (m + 1)); return i < 0 ? null : arr[i]; });
  };
  var opcAnios = A.x.slice().reverse().map(function (y) { return { v: y, txt: y }; });
  var junta = function (y) { var i = J.x.indexOf(y); return i < 0 ? null : J.v[i]; };
  var nTr = TR.x.length - 1;
  var trimAnterior = function (q) { return q ? (+q.slice(0, 4) - 1) + q.slice(4) : null; };

  /* ------------------------------------------------------------- Secciones */

  var SECCIONES = [

    /* ================================================= 1. Evolución ====== */
    {
      id: 'evolucion', nombre: 'Evolución',
      titulo: 'Residuos recogidos en Marbella',
      desc: 'Toneladas recogidas en Marbella por fracción, según el informe histórico que publica costadelsol.eco, el portal del Complejo Ambiental Costa del Sol ' +
        '(Mancomunidad de la Costa del Sol Occidental y Urbaser). R.U. son los residuos urbanos no separados; envases, papel-cartón y vidrio, la recogida selectiva.',
      render: function () {
        var q = TR.x[nTr], i0 = TR.x.indexOf(trimAnterior(q));
        return {
          hero: {
            valor: deAnio('total', ultAnio), label: 'Toneladas de residuos recogidas en ' + ultAnio, formato: tF,
            extra: [
              { label: 'Sobre ' + penAnio, valor: varPct('total', ultAnio, penAnio), formato: function (v) { return F.signo(v) + ' %'; } },
              { label: 'Recogida selectiva', valor: deAnio('pct_selectiva', ultAnio), formato: pctF },
              { label: 'R.U. por habitante y día (dato de la fuente)', valor: deAnio('kg_hab_dia_resto_fuente', ultAnio), formato: function (v) { return F.num(v, 2) + ' kg'; } },
              { label: 'R.U. · ' + Obs.periodo(q, 'trim'), valor: TR.resto[nTr], formato: tF }
            ]
          },
          kpis: [
            { label: 'R.U. · ' + ultAnio, valor: deAnio('resto', ultAnio), unidad: 't', delta: varPct('resto', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, invertir: true, serie: A.resto },
            { label: 'Envases · ' + ultAnio, valor: deAnio('envases', ultAnio), unidad: 't', delta: varPct('envases', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, serie: A.envases },
            { label: 'Papel-cartón · ' + ultAnio, valor: deAnio('papel', ultAnio), unidad: 't', delta: varPct('papel', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, serie: A.papel },
            { label: 'Vidrio · ' + ultAnio, valor: deAnio('vidrio', ultAnio), unidad: 't', delta: varPct('vidrio', ultAnio, penAnio), deltaRef: 'sobre ' + penAnio, serie: A.vidrio },
            { label: 'R.U. · ' + Obs.periodo(q, 'trim'), valor: TR.resto[nTr], unidad: 't',
              delta: i0 >= 0 && TR.resto[i0] ? (TR.resto[nTr] - TR.resto[i0]) / TR.resto[i0] * 100 : null,
              deltaRef: 'sobre ' + Obs.periodo(trimAnterior(q), 'trim'), invertir: true }
          ],
          cards: [
            {
              titulo: 'Toneladas por fracción', sub: 'Años completos',
              chips: [CH_ANUAL], fuente: F_ECO, ancho: 'full',
              spec: {
                type: 'stack', xType: 'anual', x: A.x, yFormat: 'num', unidad: 't',
                series: [
                  { name: 'R.U.', data: A.resto },
                  { name: 'Envases', data: A.envases },
                  { name: 'Vidrio', data: A.vidrio },
                  { name: 'Papel-cartón', data: A.papel }
                ]
              }
            },
            {
              titulo: 'Residuos por trimestre', sub: 'Toneladas; incluye el trimestre en curso que publica la web',
              chips: [CH_TRIM], fuente: F_ECO, ancho: 'full',
              nota: 'Los trimestres cerrados salen del informe anual; los del año en curso, del bloque que la web muestra al cerrar cada trimestre y que este observatorio guarda. ' +
                'Un hueco significa que la web cambió de trimestre antes de que se guardara.',
              spec: {
                type: 'stack', xType: 'trim', x: TR.x, yFormat: 'num',
                series: [
                  { name: 'R.U.', data: TR.resto },
                  { name: 'Envases', data: TR.envases },
                  { name: 'Vidrio', data: TR.vidrio },
                  { name: 'Papel-cartón', data: TR.papel }
                ]
              }
            },
            {
              titulo: 'Recogida selectiva', sub: 'Envases, papel-cartón y vidrio sobre el total recogido',
              chips: [CH_ANUAL], fuente: F_ECO,
              nota: 'Mide lo que se separa en el contenedor, no lo que acaba reciclado.',
              spec: { type: 'bar', xType: 'anual', x: A.x, yFormat: 'pct', series: [{ name: '% selectiva', data: A.pct_selectiva }] }
            },
            {
              titulo: 'Recogida selectiva por habitante', sub: 'Kilos por habitante y año',
              chips: [CH_ANUAL], fuente: F_ECO,
              nota: 'Toneladas del informe entre el censo que usa el propio informe.',
              spec: {
                type: 'line', xType: 'anual', x: A.x, yFormat: 'dec1', desdeCero: true,
                series: [
                  { name: 'Envases', data: A.kg_hab_anio_envases },
                  { name: 'Vidrio', data: A.kg_hab_anio_vidrio },
                  { name: 'Papel-cartón', data: A.kg_hab_anio_papel }
                ]
              }
            },
            {
              titulo: 'Kilos por habitante y día', sub: 'Marbella frente a la media andaluza de la Junta',
              chips: [CH_ANUAL], fuente: F_CALC, ancho: 'full',
              nota: 'Marbella, R.U.: el ratio que publica costadelsol.eco. Marbella, total: las cuatro fracciones entre el mismo censo. ' +
                'Andalucía: residuos de competencia local, Junta de Andalucía. La diferencia es, sobre todo, la población que no figura en el censo.',
              spec: {
                type: 'line', xType: 'anual', x: A.x, yFormat: 'dec2', desdeCero: true,
                series: [
                  { name: 'Marbella, total', data: A.kg_hab_dia },
                  { name: 'Marbella, R.U.', data: A.kg_hab_dia_resto_fuente },
                  { name: 'Andalucía (Junta)', data: A.x.map(function (y) { var v = junta(y); return v == null ? null : +(v / 365).toFixed(2); }) }
                ]
              }
            }
          ]
        };
      }
    },

    /* ================================================== 2. Mensual ====== */
    {
      id: 'mensual', nombre: 'Mes a mes',
      titulo: 'Estacionalidad de los residuos',
      desc: 'Toneladas de cada mes. En Marbella el verano dispara la basura: es la huella de la población que no figura en el censo.',
      render: function () {
        var porFraccion = function (y) {
          return {
            type: 'stack', xType: 'cat', x: MES_CORTO, yFormat: 'num', xTodas: true, unidad: 't',
            series: [
              { name: 'R.U.', data: mesesDe(M.resto, y) },
              { name: 'Envases', data: mesesDe(M.envases, y) },
              { name: 'Vidrio', data: mesesDe(M.vidrio, y) },
              { name: 'Papel-cartón', data: mesesDe(M.papel, y) }
            ]
          };
        };
        var comparaAnios = function (y) {
          var y0 = String(+y - 1);
          return { type: 'line', xType: 'cat', x: MES_CORTO, yFormat: 'num', xTodas: true,
                   series: (A.x.indexOf(y0) >= 0 ? [{ name: y0, data: mesesDe(M.resto, y0) }] : []).concat([{ name: y, data: mesesDe(M.resto, y) }]) };
        };
        var tot = mesesDe(M.total, ultAnio);
        var mx = Math.max.apply(null, tot), mn = Math.min.apply(null, tot);
        return {
          kpis: [
            { label: 'Mes de más residuos · ' + ultAnio + ' (' + MES_CORTO[tot.indexOf(mx)] + ')', valor: mx, unidad: 't' },
            { label: 'Mes de menos residuos · ' + ultAnio + ' (' + MES_CORTO[tot.indexOf(mn)] + ')', valor: mn, unidad: 't' },
            { label: 'Pico sobre valle · ' + ultAnio, valor: mn ? (mx / mn - 1) * 100 : null, unidad: '%', dec: 0 }
          ],
          cards: [
            {
              titulo: 'Residuos por mes y fracción', sub: 'Toneladas',
              chips: [CH_MES], fuente: F_ECO, ancho: 'full',
              control: { label: 'Año', valor: ultAnio, opciones: opcAnios, spec: porFraccion },
              spec: porFraccion(ultAnio)
            },
            {
              titulo: 'R.U.: un año frente al anterior', sub: 'Toneladas de residuos urbanos no separados',
              chips: [CH_MES], fuente: F_ECO,
              control: { label: 'Año', valor: ultAnio, opciones: opcAnios, spec: comparaAnios },
              spec: comparaAnios(ultAnio)
            },
            {
              titulo: 'Recogida selectiva cada mes', sub: 'Porcentaje sobre el total recogido',
              chips: [CH_MES], fuente: F_ECO,
              spec: { type: 'line', xType: 'mes', x: M.x, yFormat: 'pct', series: [{ name: '% selectiva', data: M.pct_selectiva }] }
            },
            {
              titulo: 'Serie mensual completa', sub: 'Toneladas de R.U. y de recogida selectiva',
              chips: [CH_MES], fuente: F_ECO, ancho: 'full',
              spec: { type: 'line', xType: 'mes', x: M.x, yFormat: 'num', zoom: true,
                      series: [{ name: 'R.U.', data: M.resto }, { name: 'Selectiva', data: M.selectiva }] }
            }
          ]
        };
      }
    },

    /* ============================================ 3. Población flotante == */
    {
      id: 'poblacion', nombre: 'Población flotante',
      titulo: 'Cuánta gente vive de verdad en Marbella',
      desc: 'Si cada persona generara lo que un andaluz medio según la Junta de Andalucía, los residuos de Marbella equivaldrían a una población mayor que la censada. ' +
        'Población equivalente = residuos recogidos ÷ kilos por habitante de Andalucía. Población flotante = equivalente − censo.',
      render: function () {
        var iU = PA.x.indexOf(ultAnio);
        var pico = function (y) {
          var v = mesesDe(P.flotante, y), mx = -Infinity, m = -1;
          v.forEach(function (x, k) { if (x != null && x > mx) { mx = x; m = k; } });
          return { v: m >= 0 ? mx : null, mes: m >= 0 ? MES_CORTO[m] : '—' };
        };
        var perfil = function (y) {
          return { type: 'bar', xType: 'cat', x: MES_CORTO, yFormat: 'num', xTodas: true,
                   series: [{ name: 'Población flotante ' + y, data: mesesDe(P.flotante, y) }] };
        };
        var pk = pico(ultAnio);
        var TW = PA.trimestres_web || { x: [] };
        var notas = Object.keys(PA.notas || {}).sort().map(function (k) { return PA.notas[k]; });
        return {
          nota: '<b>Es una estimación, no un censo.</b> Supone que visitantes y residentes no censados generan lo mismo que un andaluz medio. ' +
            'Sobrestima si hoteles, restaurantes y comercios generan por encima de la media andaluza; subestima si parte de sus residuos va por gestores privados. ' +
            (notas.length ? 'Notas: ' + notas.join('; ') + '.' : ''),
          notaTipo: 'warn',
          hero: {
            valor: iU >= 0 ? PA.flotante[iU] : null, label: 'Población flotante media en ' + ultAnio,
            extra: [
              { label: 'Censo ' + ultAnio, valor: iU >= 0 ? PA.censo[iU] : null },
              { label: 'Población equivalente ' + ultAnio, valor: iU >= 0 ? PA.equivalente[iU] : null },
              { label: 'Pico mensual ' + ultAnio + ' (' + pk.mes + ')', valor: pk.v },
              { label: 'Estimada · ' + Obs.periodo(TW.x[TW.x.length - 1], 'trim'), valor: TW.flotante && TW.flotante.length ? TW.flotante[TW.flotante.length - 1] : null }
            ]
          },
          cards: [
            {
              titulo: 'Población equivalente frente a censo', sub: 'Personas, cada mes',
              chips: [CH_MES, CH_EST], fuente: F_CALC, ancho: 'full',
              spec: { type: 'line', xType: 'mes', x: P.x, yFormat: 'num', desdeCero: true,
                      series: [{ name: 'Población equivalente por residuos', data: P.equivalente }, { name: 'Censo', data: P.censo }] }
            },
            {
              titulo: 'Población flotante por meses', sub: 'Equivalente menos censados',
              chips: [CH_MES, CH_EST], fuente: F_CALC,
              control: { label: 'Año', valor: ultAnio, opciones: opcAnios, spec: perfil },
              spec: perfil(ultAnio)
            },
            {
              titulo: 'Población flotante media anual', sub: 'Personas por encima del censo',
              chips: [CH_ANUAL, CH_EST], fuente: F_CALC,
              spec: { type: 'bar', xType: 'anual', x: PA.x, yFormat: 'num', series: [{ name: 'Población flotante', data: PA.flotante }] }
            },
            {
              titulo: 'Censo y población equivalente', sub: 'Media anual',
              chips: [CH_ANUAL, CH_EST], fuente: F_CALC,
              spec: { type: 'bar', xType: 'anual', x: PA.x, yFormat: 'num',
                      series: [{ name: 'Censo', data: PA.censo }, { name: 'Equivalente por residuos', data: PA.equivalente }] }
            },
            {
              titulo: 'Ratio de referencia de la Junta', sub: 'Residuos de competencia local por habitante y año, Andalucía',
              chips: [CH_ANUAL], fuente: F_JUNTA, ancho: 'full',
              nota: 'Serie completa de la edición ' + (J.edicion || '') + ' del Informe de Medio Ambiente en Andalucía. El cálculo usa solo los años con datos de Marbella.',
              spec: { type: 'bar', xType: 'anual', x: J.x, yFormat: 'dec1', unidad: 'kg',
                      series: [{ name: 'kg por habitante y año', data: J.v }] }
            }
          ]
        };
      }
    },

    /* ============================================ 4. Fuentes y método ==== */
    {
      id: 'metodo', nombre: 'Fuentes y método',
      titulo: 'De dónde sale cada cifra y qué ha cambiado',
      desc: 'Todo lo que se mide en Marbella sale de una sola fuente. La Junta de Andalucía solo aporta la vara de medir de la población flotante.',
      render: function () {
        var fila = function (t, d) { return '<p style="margin:0 0 12px"><b>' + t + '</b> ' + d + '</p>'; };
        return {
          nota:
            fila('Residuos de Marbella y censo.', 'Informe histórico de <a href="https://costadelsol.eco/marbella/#histrico" target="_blank" rel="noopener">costadelsol.eco</a>, ' +
              'el portal del Complejo Ambiental Costa del Sol (Mancomunidad de la Costa del Sol Occidental y Urbaser): meses por fracción desde 2020 y el censo de cada año, ' +
              'que coincide con el padrón del INE. El trimestre en curso sale del bloque que la misma web publica al cerrar cada trimestre.') +
            fila('Ratio andaluz.', 'Serie "Generación de residuos de competencia local" del <a href="' + (J.pagina || '#') + '" target="_blank" rel="noopener">Informe de Medio Ambiente en Andalucía</a> de la Junta, edición ' + (J.edicion || '') +
              ', en kilos por habitante y año. Solo se usa para calcular la población equivalente.') +
            fila('Cómo se actualiza.', 'Cada lunes un proceso automático revisa las dos fuentes. El informe de costadelsol.eco se publica una vez al año (el de ' + ultAnio + ' salió en febrero del año siguiente); ' +
              'el trimestre en curso, al cerrar cada trimestre; la Junta publica una edición nueva al año. Cuando cualquiera cambia, el panel se actualiza solo, sin tocar nada.') +
            '<h4 style="margin:18px 0 8px">Cambios de medida y avisos</h4>' +
            fila('La Junta ha revisado cifras antiguas.', 'Por ejemplo, 2017 figuraba con 476 kg por habitante en su ficha de 2018 y figura con 516,6 kg en la edición 2025; la Junta no explica el cambio en esa página. ' +
              'Por eso se usa siempre la serie completa de la última edición y nunca se mezclan cifras de ediciones distintas.') +
            fila('La Junta publica con un año de retraso.', 'Mientras no salga el dato de ' + ultAnio + ', ese año se calcula con el último publicado (' + (J.x[J.x.length - 1] || '—') + '). ' +
              'Cuando se publique, la población flotante de ese año se recalcula sola.') +
            fila('Qué cuenta cada fuente.', 'La Junta mide todos los residuos de competencia local; el informe de Marbella, cuatro fracciones (R.U., envases, papel-cartón y vidrio). ' +
              'Ninguna de las dos fuentes detalla si hay fracciones en una que no estén en la otra.') +
            fila('Errata en el informe de Marbella.', 'En papel-cartón de 2023 los doce meses suman 2.934.585 kg y el total del informe dice 2.938.585 kg. Se usan los meses.') +
            fila('Trimestres.', 'La web solo muestra el último trimestre. El primer trimestre de 2026 no llegó a guardarse porque el observatorio empezó a funcionar en el tercero; aparece como hueco.') +
            fila('Antes de 2020.', 'costadelsol.eco no publica años anteriores a 2020, así que el panel empieza ahí. La Mancomunidad publicó PDF de 2014 a 2019, ' +
              'y para el mismo año 2020 da otra cifra de R.U. (124.259 t frente a las 111.637 t de costadelsol.eco) sin que ninguna de las dos explique la diferencia, así que no se mezclan.')
        };
      }
    }
  ];

  /* ------------------------------------------------------------- Arranque */

  var ICONO = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M5 6l1 14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-14"/><path d="M10 11v6M14 11v6"/></svg>';

  Obs.init({
    titulo: 'Observatorio de Residuos · Marbella',
    subtitulo: 'Recogida por fracción, reciclaje y población flotante estimada · actualización automática',
    icono: ICONO,
    secciones: SECCIONES,
    actualizado: (D.meta || {}).actualizado,
    fuentes: [F_ECO, F_JUNTA],
    metodologia: 'Un proceso automático (<code>pipeline/build_data.py</code>) revisa cada lunes costadelsol.eco y la Junta de Andalucía y recalcula el panel. ' +
      'Las filas del informe se validan comprobando que los doce meses sumen el total que da la propia tabla. Detalle en la pestaña Fuentes y método.',
    pie: 'Residuos y censo: costadelsol.eco (Complejo Ambiental Costa del Sol, Mancomunidad de la Costa del Sol Occidental y Urbaser). ' +
      'Ratio andaluz: Junta de Andalucía. La población flotante es una estimación de este observatorio, no una cifra oficial.'
  });

  var m = D.meta || {};
  Obs.estado('Mensual hasta ' + Obs.periodo(m.ultimo_periodo, 'mes') + ' · trimestral hasta ' + Obs.periodo(m.ultimo_trimestre, 'trim') +
    ' · Junta hasta ' + (m.junta_ultimo || '—'), 'live');

})();
