# specs/

Estas especificaciones (`001-preprocesamiento`, `002-variables`, `003-torneo`) vienen de la rama de la compañera (`companera/main`)
y describen **su** implementación: `config.py`, `build_preprocessor()` en `features/preprocessing.py` y `add_features()`.

La versión que usan los notebooks y las pruebas de este repositorio es otra: `clean()` en `src/proyecto/data/cleaning.py`,
`FeatureOptions` y `build_preprocessor()` en `src/proyecto/features/engineering.py` y los modelos en `src/proyecto/models/`.
Las especificaciones se conservan como registro de las decisiones, pero **los nombres de funciones pueden no coincidir** con el código actual.

Diferencias principales respecto de lo que dicen estos archivos (2026-11-05):
- `Policy_Sales_Channel` se elimina en `clean()` (D13).
- `Gender` se conserva en el modelo (D12).
- El entrenamiento tiene 304.887 clientes (los conteos de 304.238 o 304.710 que aparecen en otros archivos no son correctos).
- Las decisiones vigentes están en `reports/decisiones_del_grupo.md`.
