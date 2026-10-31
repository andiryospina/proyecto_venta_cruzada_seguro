# Especificación: Torneo de modelos (`003-torneo`)

**Fecha:** 2026-10-31 · **Estado:** aprobado por el grupo (2026-10-31), con el cambio de RF-05
**Entrada:** `reports/00_caso.md` (métricas y línea base) · Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2 ·
Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/models/train.py`

## Qué se quiere

Construir `src/proyecto/models/train.py`. Con ese archivo, el notebook `05_torneo.ipynb` entrena **5 modelos** y los compara con **2 líneas base**, usando:
- los mismos datos (`data/processed/train.parquet`);
- los mismos 5 pliegues;
- las mismas métricas.

El resultado son **1 o 2 finalistas** para optimizar. **La prueba no se abre.**

## Candidatos

| # | Modelo | Por qué |
|---|---|---|
| — | Línea base 1: clase más frecuente (`DummyClassifier`) | Referencia mínima: nunca llama a nadie |
| — | Línea base 2: **regla de negocio** (llamar si no tiene seguro y tuvo daño) | Es la mejor estrategia sin modelo (costo 0,373): es la línea base que **de verdad** hay que vencer |
| 1 | Regresión logística | Simple e interpretable; probabilidades bien calibradas |
| 2 | Árbol de decisión (profundidad limitada) | El más fácil de explicar al negocio |
| 3 | Random forest | Bosque: capta relaciones no lineales (edad en campana, región) |
| 4 | LightGBM | Boosting rápido con 300.000 filas |
| 5 | XGBoost | Segundo boosting, para comparar |

**Sin balanceo de clases** (`class_weight`): la decisión ya se ajusta con el umbral de costo (P > 1/6). Balancear distorsionaría las probabilidades y movería ese umbral.

## Validación

`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` sobre entrenamiento. Se parte por fila porque cada cliente aparece una sola vez. Los pliegues se calculan **una vez** y se reutilizan para todos los modelos. Se guarda **una fila por pliegue y modelo**.

## Métricas (las dos familias, siempre)

- **Negocio (decide):**
  - `cost`: costo esperado por cliente con la matriz `[[0, 1], [5, 0]]`, decidiendo con P(interesado) > 1/6. Menor es mejor.
  - Se reporta también `cost_at_05`, el costo con umbral 0,5, para mostrar cuánto aporta el umbral de negocio.
  - `contact_rate`: % de clientes a los que se llamaría.
- **Técnicas:**
  - **PR-AUC (principal técnica)**, ROC-AUC, recall, precisión, F1 y exactitud balanceada de "interesado".
  - % de interesados capturados al llamar al 20 / 30 / 50 % mejor puntuado.
  - Log loss y Brier (calibración).

## Requisitos

- RF-01 Todo el preprocesamiento va dentro del `Pipeline` y se ajusta en cada pliegue solo con su parte de entrenamiento.
- RF-02 `build_pipeline(model, use_engineered=False, use_gender=True)` reutiliza `build_preprocessor` y `add_features`.
- RF-03 Las funciones de costo, decisión y métricas tienen pruebas con casos hechos a mano.
- RF-04 Resultados por pliegue en `reports/05_torneo_folds.csv` y conclusiones en `reports/05_torneo.md`.
- RF-05 **Cambio del grupo (2026-10-31):** primero se miden las 5 variables nuevas en la etapa 04 (`notebooks/04_features.ipynb`), con LightGBM fijo, los mismos pliegues y el costo. Se prueba una variante por variable y otra con las 5 juntas. La regla es conservar una variable si mejora / ruido > 1. Después, **el torneo usa las variables nuevas**. Resultado en `reports/04_features.md`.
- RF-06 La diferencia se traduce a **costo por cada 10.000 clientes evaluados**. No hay cifra real de volumen mensual: el grupo puede reemplazarla.
