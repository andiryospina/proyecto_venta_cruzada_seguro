# Tareas: App de Streamlit con pestañas (`008-app-streamlit`)

**Entrada:** `specs/008-app-streamlit/plan.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md`
**Estado:** borrador. Una tarea se marca `[x]` solo cuando su comprobación pasa. **Ninguna tarea toca `data/`, `models/*.joblib`,
`models/input_schema.json`, `notebooks/` ni el contenido de `reports/`.**

## Fase 1 · Funciones de `src/` (primero la prueba)

- [x] T001 Escribir `tests/test_reporting.py` (debe fallar: el módulo no existe). Cubre: `read_*` con archivo ausente → `None`; `split_sections` (ignora `#` en
  código); `find_section` con subsecciones; `strip_title`; `pick_bullets`; `list_pending` (cerrada vs abierta); `format_number`/`format_percent`;
  `build_metric_cards` (valores iguales al JSON, omite claves ausentes, sin ceros inventados); `sensitivity_rows`; `segments_by_variable`.
- [x] T002 Crear `src/proyecto/reporting/__init__.py` y `documents.py`; las pruebas de documentos pasan.
- [x] T003 Crear `src/proyecto/reporting/metrics.py`; las pruebas de métricas pasan.
- [x] T004 Una prueba contra los **archivos reales** del repositorio: la sección 3.1, las viñetas de la ficha, la sección B con P01 a P12 y las tarjetas existen
  (si alguien cambia un título, falla aquí y no en la nube).

## Fase 2 · Interfaz (Historias 1 a 5)

- [x] T005 Refactorizar `app/streamlit_app.py`: el formulario pasa tal cual a `render_predict_tab()`; cabecera con título y subtítulo; `st.tabs` con las 8 pestañas.
- [x] T006 Ayudantes de lectura con caché y `show_markdown` con aviso si falta el archivo (pestañas 1 a 3 y subpestañas 4 y 6).
- [x] T007 Bloque "Avisos importantes" sobre las pestañas (Historia 3).
- [x] T008 Pestaña 5: tarjetas, aviso 3.1, sensibilidad, imágenes, segmentos e informe completo en desplegable (Historia 2).
- [x] T009 Pestaña 7: sección B destacada con fichas P01 a P12, y A/estados/hoja de cierre en desplegables (Historia 5).
- [x] T010 Ampliar `tests/test_app.py`: las 8 pestañas cargan sin excepción y muestran contenido; avisos visibles; tarjetas del JSON; aviso con una raíz sin archivos; las
  3 pruebas originales no se tocan.

## Fase 3 · Verificación y entrega

- [x] T011 Suite completa en verde (`pytest`, sin caché), con el número de pruebas.
- [ ] T012 `git check-ignore -v` sobre cada archivo que la app lee: vacío. `git grep` de secretos sobre los cambios: vacío. `requirements.txt` sin cambios.
- [ ] T013 Arrancar la app en local (puerto 8599), capturas con `cdp_check.py` (inicio y con `click`), revisarlas; cerrar el servidor.
- [ ] T014 Revisión con las listas de los agentes (fuga, pruebas, código de la IA) y con `checklist-revision-ia.md`; anotar hallazgos.
- [ ] T015 `speckit-analyze` a mano: coherencia entre spec, plan y tareas; commit final en la rama `008-app-streamlit` (sin `push`).
