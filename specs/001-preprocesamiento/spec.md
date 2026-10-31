# Especificación: Preprocesamiento (limpieza, atípicos y partición)

**Pieza:** `001-preprocesamiento` · **Fecha:** 2026-10-31 · **Estado:** aprobada por el grupo (2026-10-31)
**Entrada:** `especificaciones/03-preprocesamiento.md` (contrato detallado, manda sobre este resumen) · `reports/01_eda.md`

## Qué se quiere

Convertir `dataset.csv` en datos limpios y partidos, listos para el torneo de modelos, aplicando **exactamente** las decisiones del EDA y
las decisiones de negocio sobre atípicos, con una prueba automática por regla.

## Historias de usuario

- **US1 (P1) · Limpieza reproducible.** Como analista, quiero una función `clean(df)` que aplique las reglas sin aprendizaje (códigos a
  entero, categorías a números, marca de prima mínima, valores imposibles a vacío) sin borrar filas, para regenerar los datos desde cero.
  *Aceptación:* con el dataset real, `clean` devuelve 381.109 filas, 13 columnas, sin texto, y `is_min_premium` suma 64.877.
- **US2 (P1) · Partición honesta.** Como analista, quiero partir 80/20 estratificado por `Response` con semilla 42 y quitar repetidos
  solo en entrenamiento, para medir el modelo sin fuga. *Aceptación:* ningún `id` en ambos lados; 76.222 filas en prueba; tasa de
  `Response` igual (± 0,1 pp); prueba sin modificar.
- **US3 (P2) · Atípicos y categorías raras dentro del `Pipeline`.** Como analista, quiero un preprocesador que recorte la prima al p99,9
  de entrenamiento, aplique `log1p`, agrupe categorías raras y escale, ajustado solo con entrenamiento. *Aceptación:* el tope se aprende
  del entrenamiento, una categoría nueva no rompe la transformación y la salida no tiene vacíos.

## Requisitos

- RF-01 `data/raw/` y `dataset.csv` nunca se modifican.
- RF-02 Ninguna regla con aprendizaje (cuantiles, categorías, medianas, escalado) se ajusta antes de partir.
- RF-03 Cada regla tiene una función en `src/proyecto/` y al menos una prueba en `tests/` con datos hechos a mano.
- RF-04 El notebook `03_preprocesamiento.ipynb` solo orquesta: importa de `src/`, no define lógica.
- RF-05 Salidas: `data/processed/train.parquet` y `data/processed/test.parquet` (no se versionan).

## Fuera de alcance

Selección de variables, creación de nuevas variables (etapa 04), entrenamiento de modelos y elección de umbral.
