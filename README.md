# Observatorio de Residuos · Marbella

Residuos recogidos en Marbella por año, mes y fracción (resto, envases, vidrio y
papel-cartón), recogida selectiva y población flotante estimada.

**Web:** https://josehino.github.io/observatorio-residuos-marbella/

## Fuentes

| Fuente | Qué da |
|---|---|
| Mancomunidad de Municipios de la Costa del Sol Occidental · PDF "Datos residuos AAAA" | toneladas mensuales de Marbella por fracción (Complejo Ambiental Costa del Sol, gestionado por Urbaser). Publicados 2014-2020 completos y enero-febrero de 2021 |
| Mancomunidad · notas de balance anual | kg por habitante y día de Marbella (2023, 2025) |
| INE · Padrón municipal (serie `DPOP13669`) | población empadronada a 1 de enero |
| Junta de Andalucía · RE01 e Informe de Medio Ambiente | kg de residuos municipales por habitante y año en Andalucía (declarados en `pipeline/build_data.py` con su fuente) |

## Población flotante

Población equivalente = residuos recogidos ÷ ratio andaluz por habitante.
Población flotante = equivalente − padrón. Es una estimación, no una cifra oficial.

## Actualización

La Action corre cada lunes, revisa la web de la Mancomunidad y el INE, y hace
commit solo si cambian las cifras.
