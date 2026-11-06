# Tareas: Validación final con el conjunto de prueba (`005-validacion`)

**Entrada:** `specs/005-validacion/plan.md` · **Estado:** aprobado por el grupo (2026-11-05)
Una tarea se marca `[x]` solo cuando su prueba pasa (`pytest tests`). **La prueba no se abre antes de T007.**

- [x] T001 Agregar `AGE_BANDS`, `MIN_REGION_SIZE = 1000`, `SENSITIVITY_RATIOS = (3, 5, 10)` y `TEST_MARKER` a `src/proyecto/config.py`;
  `models/final_pipeline.joblib` a `.gitignore`.
- [x] T002 [P] Escribir `tests/test_validation.py` (primero, debe fallar). Debe cubrir:
  - `should_calibrate`: `True` si el intervalo de la diferencia de log loss está todo bajo cero y el costo no sube; `False` si el intervalo
    cruza el cero; `False` si el costo sube (enmienda 2026-11-05: mejora mínima del log loss);
  - `bootstrap_log_loss_difference`: 0 con probabilidades idénticas; intervalo bajo cero con probabilidades claramente mejores;
  - `open_test_once`: con la marca ya creada lanza error **sin leer** el archivo; con una decisión vacía lanza error; la primera vez escribe
    la marca con fecha y commit y devuelve los datos (con archivos temporales, nunca con la prueba real);
  - `bootstrap_mean`: el intervalo contiene el promedio; reproducible con la misma semilla; intervalo de ancho 0 con valores constantes;
  - `age_band`: límites 29/30, 44/45, 59/60 caen en el tramo correcto;
  - `segment_table`: cuentas, % contactado y % real correctos en un ejemplo pequeño; los segmentos chicos se agrupan como "otras";
  - `cost_sensitivity`: con razón 5 coincide con `expected_cost`; con razón 10 el costo de los falsos negativos se duplica;
  - línea base: `BusinessRuleClassifier` ajustado + `decide` llama exactamente a quienes cumplen la regla.
- [x] T003 Crear `src/proyecto/models/validation.py` con las funciones del plan; `pytest tests/test_validation.py` en verde.
- [x] T004 Notebook 07, secciones 0–1: cargar `train.parquet`, `ID_COL = "id"`, `TARGET = "Response"`; decisiones congeladas con
  fecha y hora. El notebook las guarda en `reports/07_decisiones_congeladas.json` (constancia con hora, antes de abrir la prueba);
  se copian a la sección 1 de `reports/07_validacion.md` en T011.
- [x] T005 Notebook 07, sección 2: calibración con la reserva de la etapa 06 → `should_calibrate` → `reports/07_calibracion.png`.
- [x] T006 Notebook 07, sección 3: modelo final con todo el entrenamiento → `models/final_pipeline.joblib`.
- [x] T007 Notebook 07, secciones 4–5: `open_test_once` → métricas del modelo y de la línea base, intervalos, diferencia y lectura
  según la regla → `reports/07_metricas_test.json`.
- [x] T008 Notebook 07, secciones 6–7: tabla por segmento → `reports/07_segmentos.csv`; sensibilidad 3/5/10; SHAP → `reports/07_shap.png`.
- [x] T009 Notebook 07, sección 8: una ejecución de MLflow (`venta-cruzada-validacion`, `etapa=07_validacion`) con todas las métricas.
- [x] T010 Ejecutar el notebook completo **una vez** y `pytest tests` en verde.
- [x] T011 Escribir `reports/07_validacion.md` con las cifras reales, la conclusión según la regla, los segmentos de alarma, la advertencia
  de atributos sensibles y los límites del modelo.
- [x] T012 Revisar el notebook 07 con el subagente `auditor-de-fuga`; anotar lo que diga en el reporte.
- [x] T013 Anotar la decisión de calibración y el resultado frente a la línea base en la sección 7 de `especificacion-proyecto.md`.
