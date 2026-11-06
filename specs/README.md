# specs/

Una carpeta por pieza de trabajo de Spec Kit, cada una con `spec.md`, `plan.md` y `tasks.md`:

| Carpeta | Pieza |
|---|---|
| `001-preprocesamiento` | Limpieza y partición (etapa 03) |
| `002-variables` | Las 5 variables nuevas (etapa 04) |
| `003-torneo` | Torneo de modelos (etapa 05) |
| `004-optimizacion` | Optimización de LightGBM con Optuna (etapa 06) |
| `005-validacion` | Validación final con la prueba (etapa 07) |
| `006-registro-modelo` | Registro del modelo en MLflow / Databricks (etapa 08) |
| `007-integracion-main` | Integración de las dos ramas del grupo sobre el modelo final (2026-11-06) |

**Desde la integración (2026-11-06, D15)** el código de `src/` es el que describen estas especificaciones: `clean()` en
`src/proyecto/data/cleaning.py`, `add_features()` en `src/proyecto/features/engineering.py`, el preprocesamiento en
`src/proyecto/features/preprocessing.py` y los modelos en `src/proyecto/models/`. El entrenamiento tiene **304.238** clientes (304.887
menos 649 perfiles repetidos, que se quitan solo del entrenamiento; P12). Las decisiones vigentes están en `reports/decisiones_del_grupo.md`;
qué se tomó de cada rama, en `reports/integracion_main.md`.

Antes de la integración, `main` tenía otra implementación (la de la compañera) y este archivo advertía que estas especificaciones no
coincidían con ella. Esa implementación sigue en la historia de Git (commit `579bf8c`).
