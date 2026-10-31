# Tareas: Variables nuevas (`002-variables`)

**Entrada:** `specs/002-variables/plan.md` · **Estado:** aprobado por el grupo (2026-10-31)
Una tarea se marca `[x]` solo cuando su prueba pasa (`pytest tests`).

- [x] T001 Agregar `YOUNG_AGE`, `PEAK_AGE`, `ENGINEERED_FLAGS` y `ENGINEERED_NUMERIC` a `src/proyecto/config.py`.
- [x] T002 [P] Escribir pruebas en `tests/test_features.py`. Deben cubrir:
  - el valor de cada variable con filas hechas a mano;
  - la división por cero o un vacío dan vacío y no infinito;
  - el original no cambia;
  - los interruptores `use_engineered` y `use_gender`;
  - el preprocesador con variables nuevas no deja vacíos;
  - una prueba de integración con la salida de `clean()`.
- [x] T003 Crear `src/proyecto/features/engineering.py` con `_ratio`, `add_features` y `feature_columns`.
- [x] T004 Adaptar `build_preprocessor` en `src/proyecto/features/preprocessing.py` a `feature_columns`, sin cambiar lo que hace cuando se llama sin argumentos.
- [x] T005 Ejecutar `pytest tests` (todas las pruebas, incluidas las 54 actuales) y volver a ejecutar el notebook 03 para confirmar que no cambia.
- [x] T006 Anotar la decisión en la sección 7 de `especificacion-proyecto.md`.
