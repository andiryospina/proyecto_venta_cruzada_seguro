# Tareas: Torneo de modelos (`003-torneo`)

**Entrada:** `specs/003-torneo/plan.md` · **Estado:** aprobado por el grupo (2026-10-31)
Una tarea se marca `[x]` solo cuando su prueba pasa (`pytest tests`).

- [x] T001 Agregar `COST_MATRIX` y `CV_FOLDS` a `src/proyecto/config.py`.
- [x] T002 [P] Escribir pruebas en `tests/test_models.py`. Deben cubrir:
  - umbral = 1/6;
  - costo 0 con predicción perfecta y costo según la matriz;
  - la decisión con el umbral;
  - `capture_at`;
  - métricas perfectas y métricas al azar;
  - `BusinessRuleClassifier`;
  - pliegues estratificados y reproducibles;
  - el pipeline entrena con la salida de `clean()`.
- [x] T003 Crear `src/proyecto/models/train.py` con las funciones del plan.
- [x] T003b `feature_columns(use_engineered=...)` acepta también una lista de variables nuevas, para medirlas una por una (con su prueba).
- [x] T003c Llenar y ejecutar `notebooks/04_features.ipynb`: referencia, cada variable sola, las 5 juntas; tabla mejora / ruido → `reports/04_features.md`.
- [x] T004 Llenar `notebooks/05_torneo.ipynb` (con las variables nuevas): cargar los datos, armar los pliegues, correr el torneo y producir:
  - el resumen;
  - la gráfica por pliegue;
  - las métricas técnicas;
  - el ranking de negocio frente al técnico;
  - la comparación pareada;
  - el costo por cada 10.000 clientes;
  - los finalistas.
- [x] T005 Ejecutar el notebook y `pytest tests` en verde.
- [x] T006 Escribir `reports/05_torneo.md` y `reports/05_torneo_folds.csv` con las cifras reales y los finalistas.
- [x] T007 Anotar la decisión en la sección 7 de `especificacion-proyecto.md`.
