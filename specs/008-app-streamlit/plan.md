# Plan: App de Streamlit con pestañas (`008-app-streamlit`)

**Fecha:** 2026-11-06 · **Spec:** `specs/008-app-streamlit/spec.md` · **Estado:** borrador

## Revisión contra la constitución

| Principio | Cómo se cumple |
|---|---|
| I, II, III | No se toca `data/`, no se parte ni se abre ninguna prueba; la app solo **lee** cifras ya publicadas. |
| IV | Cada función nueva de `src/proyecto/reporting/` tiene prueba en `tests/test_reporting.py`; las pestañas, en `tests/test_app.py`. |
| V | La app no lee `.env` ni llama a Databricks; no importa `mlflow`, `optuna` ni `shap`. |
| VI | La lógica va en `src/`; `app/streamlit_app.py` solo dibuja. Revisión con `checklist-revision-ia.md` (ver "Revisión"). |
| VII | Ninguna cifra a mano: todo sale de `reports/` y `models/`. Los avisos se extraen, no se reescriben. |

La constitución aún tiene corchetes sin llenar; no se edita (fuera de alcance).

## Diseño

```text
src/proyecto/reporting/__init__.py        # NUEVO
src/proyecto/reporting/documents.py       # NUEVO: leer archivos y partir markdown (sin Streamlit)
src/proyecto/reporting/metrics.py         # NUEVO: formato, tarjetas, sensibilidad y segmentos desde JSON/CSV
tests/test_reporting.py                   # NUEVO: una o más pruebas por función
app/streamlit_app.py                      # REFACTOR: 8 pestañas; el formulario pasa a render_predict_tab()
tests/test_app.py                         # AMPLIADO: pestañas nuevas (las 3 pruebas existentes no cambian)
```

### Funciones de `documents.py`

| Función | Qué hace |
|---|---|
| `read_text(path)` / `read_json(path)` / `read_csv(path)` | Devuelven el contenido o `None` si el archivo no existe o no se puede leer (nunca lanzan por ausencia) |
| `split_sections(markdown, level)` | Parte un markdown en `Section(title, level, body)` por los encabezados de un nivel (ignora los `#` dentro de bloques de código) |
| `find_section(markdown, prefix, levels=(2, 3))` | Primera sección cuyo título empieza por `prefix`; su cuerpo incluye las subsecciones hasta el siguiente encabezado del mismo nivel o menor |
| `strip_title(markdown)` | Quita la primera línea `# Título` (la pestaña pone el suyo) |
| `pick_bullets(markdown, starts)` | Viñetas de primer nivel cuyo texto empieza por alguno de `starts` (admite negritas) |
| `list_pending(markdown)` | De la sección "B." de `decisiones_del_grupo.md`: introducción y lista de `Pending(code, title, body, closed)` para cada `### Pnn ·`; `closed` si el título dice `CERRADO` |

### Funciones de `metrics.py`

| Función | Qué hace |
|---|---|
| `format_number(value, decimals)` / `format_percent(value, decimals)` | Formato con coma decimal (`0,3312`, `36,5 %`) |
| `build_metric_cards(metrics)` | Del bloque `prueba` arma `MetricCard(label, value, help)`: costo (IC 95 %), diferencia frente a la línea base (IC 95 %), % a llamar, recall, precisión, PR-AUC, ROC-AUC, captura al 20 %. Omite las que no se pueden armar; nunca rellena con ceros |
| `sensitivity_rows(metrics)` | De `prueba.sensibilidad` ("3_a_1" → "R = 3"): filas con costo del modelo, de la línea base y quién gana |
| `segments_by_variable(df)` | Agrupa `07_segmentos.csv` por `variable` y devuelve, para cada una, una tabla con encabezados en español y porcentajes formateados |

### `app/streamlit_app.py`

```text
set_page_config → título → bloque "Avisos importantes" (render_honesty_notices)
st.tabs([...8...])
  1 Caso · 2 EDA · 3 Variables · 4 Modelos (st.tabs Torneo | Optimización)
  5 Resultado (tarjetas, aviso 3.1, sensibilidad, imágenes, segmentos, informe completo en desplegable)
  6 Registro y ficha (st.tabs) · 7 Decisiones (B destacada, fichas P01..P12, A/estados/hoja de cierre en desplegables)
  8 Probar el modelo = render_predict_tab() con el formulario de siempre
```

- Las lecturas pasan por `@st.cache_data` (`load_text`, `load_json`, `load_csv`, con la fecha de modificación como parte de la clave); el modelo, por `@st.cache_resource`.
- Un único `show_markdown(relative_path, strip_title=True)` hace: leer → si es `None`, `st.warning("Falta `ruta`")`; si no, `st.markdown`.
- Sin `unsafe_allow_html` con contenido de archivos. El HTML de las tarjetas no existe: se usan `st.container(border=True)`, `st.caption` y `st.markdown` con el valor ya formateado.
- Se preserva el orden: el primer botón de la página es **Evaluar** y el primer `st.metric` es "Resultado sugerido".
- Streamlit 1.66 (la de `requirements.txt`): se usa `width="stretch"` en `st.image`.

## Decisiones técnicas

- **Subpaquete `reporting`** (no `app_content`): describe lo que hace (preparar informes para mostrar) y no depende de Streamlit, así se prueba sin la app.
- **`find_section` por prefijo** (`"3.1"`, `"Límites"`, `"B."`) y no por posición: si alguien reordena el informe, la app sigue encontrando la sección.
- **Qué hacer si la sección no existe:** la pestaña muestra el informe completo y un aviso (no rompe).
- **Sin dependencias nuevas:** `re`, `json`, `pathlib`, `dataclasses`, `pandas`.
- **Archivos ignorados por Git:** `git check-ignore -v` sobre todo lo que se lee (T012).

## Revisión (listas de los agentes, aplicadas a mano)

- **auditor-de-fuga:** no se lee `data/` ni se calcula nada con la prueba; la app muestra cifras ya registradas. Sin hallazgos esperados.
- **escritor-de-pruebas:** casos felices, vacíos (archivo ausente, JSON sin claves), y que cada cifra de una tarjeta salga del JSON.
- **revisor-de-codigo-ia / `checklist-revision-ia.md`:** funciones cortas, nombres en inglés y textos en español, sin `except` mudo que oculte errores de lógica (solo `OSError`/`ValueError` en la lectura), sin secretos.
