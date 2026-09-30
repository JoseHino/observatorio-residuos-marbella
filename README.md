# Observatorio de Residuos · Marbella

Residuos recogidos en Marbella por año, mes y fracción (R.U., envases, vidrio y
papel-cartón), recogida selectiva y población flotante estimada.

**Web:** https://josehino.github.io/observatorio-residuos-marbella/

## Fuentes

| Fuente | Qué da |
|---|---|
| [costadelsol.eco](https://costadelsol.eco/marbella/#histrico) · informe histórico de Marbella (Complejo Ambiental Costa del Sol: Mancomunidad + Urbaser) | toneladas mensuales por fracción desde 2020, censo de cada año y el trimestre en curso |
| Junta de Andalucía · Informe de Medio Ambiente ("IMA de un vistazo", hoja 10-01) | kg de residuos de competencia local por habitante y año en Andalucía, serie completa de la última edición |

Todo lo que se mide en Marbella sale de costadelsol.eco. La Junta solo aporta
el ratio para estimar la población flotante. La pestaña "Fuentes y método"
explica los cambios de medida y las erratas detectadas.

## Población flotante

Población equivalente = residuos recogidos ÷ ratio andaluz por habitante.
Población flotante = equivalente − censo. Es una estimación, no una cifra oficial.

## Actualización

La Action corre cada lunes, revisa costadelsol.eco (informe histórico y trimestre en curso) y la edición más reciente del IMA de la Junta, y hace
commit solo si cambian las cifras.
