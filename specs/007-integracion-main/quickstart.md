# Cómo comprobar la integración (`007-integracion-main`)

Desde la raíz del repositorio, con el entorno activado y `PYTHONUTF8=1`.

| # | Qué se comprueba | Comando | Qué debe salir |
|---|---|---|---|
| 1 | Pruebas | `python -m pytest -q` | Todas en verde (113 de la rama + `test_serving.py`), 0 fallas |
| 2 | Un solo modelo | Celda final del notebook 09 (ida y vuelta) | `diferencia máxima ... <= 1e-9` entre `model.joblib` y `final_pipeline.joblib` en 200 clientes de entrenamiento |
| 3 | Variables del modelo | `python -c "import sys; sys.path.insert(0,'src'); import joblib; print(list(joblib.load('models/final_pipeline.joblib').feature_names_in_))"` | Incluye `Gender`, `Vintage`, `Driving_License`; no `Policy_Sales_Channel` |
| 4 | Datos de entrenamiento | `python -c "import pandas as pd; print(len(pd.read_parquet('data/processed/train.parquet')))"` | `304238` |
| 5 | Cifras del modelo de `main` fuera de lugar | `git grep -nE '0[.,]3317|0[.,]8519|0[.,]3533' -- reports presentacion models README.md` | Solo líneas en `decisiones_del_grupo.md` o `integracion_main.md` (como historia) |
| 6 | Datos personales | `git grep -nE '@(unaula\|gmail\|hotmail\|outlook)' -- . ':!material-del-curso'` | Nada |
| 7 | La prueba no se volvió a abrir | `git grep -n "test.parquet" -- notebooks/09_inferencia.ipynb` y revisar `reports/prueba_abierta.txt` | Nada en el notebook 09; la constancia muestra solo las dos aperturas del 2026-11-05 |
| 8 | Archivos de `main` quitados | Comparar `git diff --name-status origin/main HEAD --diff-filter=D` con la tabla de `reports/integracion_main.md` | Cada archivo borrado aparece en la tabla con su motivo |
| 9 | App | `streamlit run app/streamlit_app.py` | Formulario de 9 datos (sin canal), recomendación "Llamar/No llamar" y aviso de uso responsable; edad 150 → mensaje de error |
