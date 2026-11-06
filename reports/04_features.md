# Etapa 04 · Variables nuevas: medición

> Resultado de `notebooks/04_features.ipynb`, ejecutado el 2026-10-31. Tabla completa en `reports/04_features_tabla.csv`.
> Código: `src/proyecto/features/engineering.py` y `src/proyecto/models/train.py`.

## Cómo se midió

- **Datos:** `data/processed/train.parquet`, 304.238 clientes. La prueba no se abrió.
- **Mismo modelo para todas las variantes:** LightGBM con parámetros fijos (300 árboles, tasa de aprendizaje 0,05, 31 hojas).
- **Mismos pliegues para todas las variantes:** 5 pliegues estratificados, semilla 42. Son los mismos que usa el torneo.
- **Métrica principal:** costo esperado por cliente. Usa la matriz 5 a 1 y decide llamar si P > 1/6. Menor es mejor.
- **Métrica de control:** PR-AUC.
- **Regla (escrita antes de medir):** se conserva una variable si **mejora / ruido > 1**.
  - mejora = costo de la referencia − costo de la variante;
  - ruido = desviación del costo de la variante entre pliegues.

## Resultados

| Variante | Costo | ± ruido | Mejora / ruido | Pliegues que gana | PR-AUC | Decisión según la regla |
|---|---|---|---|---|---|---|
| Referencia (variables base) | 0,33245 | 0,00269 | — | — | 0,3472 | — |
| + `uninsured_with_damage` | 0,33226 | 0,00333 | 0,06 | 3 de 5 | 0,3475 | descartar |
| + `damage_x_vehicle_age` | 0,33226 | 0,00324 | 0,06 | 3 de 5 | 0,3471 | descartar |
| + `is_young_customer` | 0,33200 | 0,00315 | 0,14 | 3 de 5 | 0,3471 | descartar |
| + `age_peak_distance` | 0,33253 | 0,00300 | −0,03 | 3 de 5 | 0,3473 | descartar |
| + `premium_per_age` | 0,33173 | 0,00296 | 0,24 | 3 de 5 | 0,3465 | descartar |
| + las 5 juntas | 0,33242 | 0,00299 | 0,01 | 3 de 5 | 0,3469 | descartar |

## Lectura

- **Ninguna variable pasa la regla.** La mayor mejora es la de `premium_per_age`: 0,0007 en costo, 4 veces menor que el ruido entre pliegues. Además empeora el PR-AUC.
- **Por qué no aportan:** LightGBM construye solo estas combinaciones a partir de las variables originales (por ejemplo, "sin seguro y con daño"). Para él no son información nueva.
- **Tampoco empeoran:** todas las diferencias están dentro del ruido.
- **Referencia útil para el torneo:** LightGBM con las variables base ya cuesta **0,332 por cliente**, frente a 0,373 de la regla de negocio (cifra de `reports/00_caso.md`, calculada sobre todo el dataset).

## Decisión del grupo

**El torneo usa las 5 variables nuevas** (`use_engineered=True`). Es una decisión del grupo del 2026-10-31 y va en contra de la regla de esta etapa.

- **Motivo:** los modelos simples del torneo (regresión logística y árbol de decisión) no descubren solos las interacciones ni la forma de campana de la edad, y podrían beneficiarse.
- **Riesgo:** casi nulo. Para LightGBM, el efecto medido es nulo.
- **Si en el torneo tampoco ayudan:** se apagan en la etapa 06.
