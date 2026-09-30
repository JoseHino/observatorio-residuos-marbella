# Observatorio de Residuos · Marbella

Residuos recogidos en Marbella por año, mes y fracción (resto, envases, vidrio y
papel-cartón), recogida selectiva y población flotante estimada.

**Web:** https://josehino.github.io/observatorio-residuos-marbella/

## Fuentes

| Fuente | Qué da |
|---|---|
| [costadelsol.eco](https://costadelsol.eco/marbella/#histrico) · informe histórico de Marbella (Complejo Ambiental Costa del Sol: Mancomunidad + Urbaser) | toneladas mensuales por fracción 2020-2025 y el trimestre en curso |
| Mancomunidad de Municipios de la Costa del Sol Occidental · PDF "Datos residuos AAAA" | toneladas mensuales por fracción 2014-2019 y total comarcal |
| INE · Padrón municipal (serie `DPOP13669`) | población empadronada a 1 de enero |
| Junta de Andalucía · RE01 e Informe de Medio Ambiente | kg de residuos municipales por habitante y año en Andalucía (declarados en `pipeline/build_data.py` con su fuente) |

**Salto de serie en 2020:** para la fracción resto, la Mancomunidad daba 124.259 t
en 2020 y costadelsol.eco 111.637 t. Envases, vidrio y papel coinciden.

## Población flotante

Población equivalente = residuos recogidos ÷ ratio andaluz por habitante.
Población flotante = equivalente − padrón. Es una estimación, no una cifra oficial.

## Actualización

La Action corre cada lunes, revisa costadelsol.eco (informe histórico y trimestre en curso), la web de la Mancomunidad y el INE, y hace
commit solo si cambian las cifras.
