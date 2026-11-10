# Investigación: App con pestañas (`008-app-streamlit`)

Comprobaciones hechas el 2026-11-06 antes de diseñar (no se supuso ningún archivo).

| Pregunta | Hallazgo | Consecuencia |
|---|---|---|
| ¿Qué archivos existen? | `reports/` tiene 00, 01, 04, 05, 06, 07 (md, json, csv, 2 png), 08, 09, decisiones, informe técnico e integración; `models/` tiene `ficha_modelo.md`, `input_schema.json` y los `.joblib` | Se usan los de la spec; faltan las etapas 02 y 03 como informe propio (están dentro del EDA) |
| ¿Están versionados? | `git check-ignore -v reports/* models/*` no marca ninguno; todos aparecen en `git ls-files` | La app desplegada los verá |
| ¿Los informes referencian las imágenes? | No (`grep '!\['` vacío) | Las imágenes se muestran con `st.image` junto a su título |
| ¿Dónde está el aviso de la prueba abierta dos veces? | `reports/07_validacion.md`, `### 3.1`; constancia en `reports/prueba_abierta.txt` | Se extrae por prefijo de título |
| ¿Dónde están las advertencias de edad y género? | `models/ficha_modelo.md`, `## Límites y usos no recomendados`, viñeta "Atributos sensibles o de uso regulado" (cobertura 48,3 % y 64,0 %) | Se extraen las viñetas por su inicio |
| ¿Cómo está estructurada la sección B? | `## B. Pendientes de dato externo`, subsecciones `### P01 ·` a `### P12 ·`; P12 dice `[CERRADO 2026-11-06]` | `list_pending` las separa y marca las cerradas |
| ¿Algún widget de la app interfiere con `tests/test_app.py`? | Las pruebas usan `at.button[0]`, `at.metric[0]` y `selectbox` con "seguro de vehículo" / "daños" | Ningún botón, `st.metric` ni selectbox con esas etiquetas fuera del formulario |
| ¿Las tablas markdown se ven bien en `st.markdown`? | Streamlit dibuja tablas GitHub | Se verifica con capturas |
| ¿Streamlit 1.66 soporta `st.tabs` anidadas y `width="stretch"`? | Sí | Subpestañas en Modelos y en Registro |
