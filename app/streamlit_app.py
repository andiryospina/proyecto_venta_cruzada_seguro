"""App del proyecto «Venta cruzada inteligente»: cuenta las 9 etapas en pestañas y conserva el formulario de predicción.

- Todo el contenido sale de `reports/` y `models/` del repositorio (principio VII: ninguna cifra escrita a mano aquí).
  Si falta un archivo, la pestaña lo avisa y las demás siguen funcionando.
- La lógica de leer informes, partir markdown y armar tarjetas vive en `src/proyecto/reporting/` (principio VI);
  este archivo solo dibuja la interfaz.
- Carga `models/model.joblib` desde ESTE repositorio. NO consulta Databricks ni lee `.env`.
- El formulario valida las entradas: si un dato es imposible, explica qué corregir en vez de responder cualquier cosa.

Ejecutar en local (desde la raíz de tu repo):  streamlit run app/streamlit_app.py
"""
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "model.joblib"
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
UNKNOWN = "(no sé)"
DEFAULT_TITLE = "Venta cruzada inteligente"

# El paquete de src/ puede llamarse `proyecto` o el nombre que le hayas puesto: lo buscamos.
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
PACKAGE = next((p.name for p in sorted(SRC.iterdir()) if p.is_dir() and (p / "__init__.py").exists()), "proyecto")
predict_module = importlib.import_module(f"{PACKAGE}.inference.predict")
schema_module = importlib.import_module(f"{PACKAGE}.inference.schema")
documents = importlib.import_module(f"{PACKAGE}.reporting.documents")
report_metrics = importlib.import_module(f"{PACKAGE}.reporting.metrics")

DEFAULT_RESPONSIBLE_USE = (
    "- Esta herramienta **apoya** una decisión; la decisión final es de una persona.\n"
    "- Fue entrenada con los datos de este proyecto: no la uses fuera de ese contexto sin validarla de nuevo.\n"
    "- Revisa los **límites del modelo** en `models/ficha_modelo.md` antes de usarla."
)

TAB_TITLES = [
    "1 · Caso de negocio", "2 · Datos y EDA", "3 · Variables", "4 · Modelos", "5 · Resultado en la prueba",
    "6 · Registro y ficha", "7 · Decisiones y pendientes", "8 · Probar el modelo",
]


# ---------- lectura de archivos (con caché; la fecha de modificación forma parte de la clave) ----------

def _stamp(relative: str) -> float:
    try:
        return (ROOT / relative).stat().st_mtime
    except OSError:
        return 0.0


@st.cache_data
def _text(relative: str, stamp: float) -> str | None:
    return documents.read_text(ROOT / relative)


@st.cache_data
def _json(relative: str, stamp: float) -> dict | None:
    return documents.read_json(ROOT / relative)


@st.cache_data
def _csv(relative: str, stamp: float) -> pd.DataFrame | None:
    return documents.read_csv(ROOT / relative)


def load_text(relative: str) -> str | None:
    return _text(relative, _stamp(relative))


def load_json(relative: str) -> dict | None:
    return _json(relative, _stamp(relative))


def load_csv(relative: str) -> pd.DataFrame | None:
    return _csv(relative, _stamp(relative))


def warn_missing(relative: str, detail: str = "") -> None:
    st.warning(f"No se pudo leer `{relative}` del repositorio. {detail}Esta parte no se puede mostrar.".replace("  ", " "))


def show_markdown(relative: str, drop_title: bool = True) -> str | None:
    """Dibuja un informe con st.markdown (sin HTML); si falta, avisa. Devuelve el texto leído."""
    text = load_text(relative)
    if text is None:
        warn_missing(relative)
        return None
    st.markdown(documents.strip_title(text) if drop_title else text)
    return text


def show_image(relative: str, caption: str) -> None:
    path = ROOT / relative
    if not path.is_file():
        warn_missing(relative)
        return
    st.image(str(path), caption=caption, width="stretch")


# ---------- avisos de honestidad (extraídos de los archivos, no reescritos) ----------

def render_notices() -> None:
    """Bloque visible sobre las pestañas: prueba abierta dos veces y uso de edad y género. (Los pendientes viven en la pestaña 7.)"""
    ficha = load_text("models/ficha_modelo.md")
    opened = load_text("reports/prueba_abierta.txt")
    with st.container(border=True):
        st.markdown("**Avisos importantes antes de usar este modelo**")
        limits = documents.find_section(ficha, "Límites")
        if ficha is None:
            warn_missing("models/ficha_modelo.md")
        elif limits is None:
            st.warning("No se encontró la sección de límites en `models/ficha_modelo.md`; léela completa en la pestaña 6.")
        else:
            bullets = documents.pick_bullets(limits.body, ["Atributos sensibles", "La prueba en el grupo"])
            st.warning("\n\n".join(bullets) if bullets else limits.body)
        if opened is not None:
            with st.expander("Constancia de apertura de la prueba cerrada (`reports/prueba_abierta.txt`)"):
                st.markdown(opened.replace("\n", "  \n"))


# ---------- pestañas de contenido ----------

def render_models_tab() -> None:
    torneo, optimizacion = st.tabs(["Torneo de modelos (etapa 5)", "Optimización (etapa 6)"])
    with torneo:
        show_markdown("reports/05_torneo.md")
    with optimizacion:
        show_markdown("reports/06_optimizacion.md")


def render_features_tab() -> None:
    show_markdown("reports/04_features.md")
    table = load_csv("reports/04_features_tabla.csv")
    if table is None:
        warn_missing("reports/04_features_tabla.csv")
    else:
        with st.expander("Tabla completa de la medición (`reports/04_features_tabla.csv`)"):
            st.dataframe(table, hide_index=True)


def render_results_tab() -> None:
    metrics = load_json("reports/07_metricas_test.json")
    validation = load_text("reports/07_validacion.md")
    st.subheader("Resultado en la prueba cerrada")
    if metrics is None:
        warn_missing("reports/07_metricas_test.json")
    else:
        test_block = metrics.get("prueba", {})
        if isinstance(test_block.get("clientes"), int) and isinstance(test_block.get("tasa_interesados"), float):
            st.caption(f"{report_metrics.format_number(test_block['clientes'], 0)} clientes que el modelo nunca vio · "
                       f"{report_metrics.format_percent(test_block['tasa_interesados'], 2)} interesados.")
        cards = report_metrics.build_metric_cards(metrics)
        if not cards:
            st.warning("`reports/07_metricas_test.json` no trae el bloque `prueba` con las métricas esperadas.")
        for start in range(0, len(cards), 3):
            for column, card in zip(st.columns(3), cards[start:start + 3]):
                with column, st.container(border=True):
                    st.caption(card.label)
                    st.markdown(f"## {card.value}")
                    if card.help:
                        st.caption(card.help)

    section = documents.find_section(validation, "3.1")
    if validation is None:
        warn_missing("reports/07_validacion.md")
    elif section is None:
        st.warning("No se encontró la sección 3.1 en `reports/07_validacion.md`; léela completa más abajo.")
    else:
        st.warning(f"**{section.title}**\n\n{section.body}")

    rows = report_metrics.sensitivity_rows(metrics)
    if rows:
        st.markdown("**Cómo cambia el costo según R** (cuánto cuesta no llamar a un comprador frente a una llamada inútil)")
        st.dataframe(pd.DataFrame(rows), hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown("**Calibración**")
        show_image("reports/07_calibracion.png", "Curva de calibración (reports/07_calibracion.png)")
    with right:
        st.markdown("**Qué variables pesan (SHAP)**")
        show_image("reports/07_shap.png", "Importancia de variables con SHAP (reports/07_shap.png)")

    st.markdown("**Errores y carga de trabajo por segmento**")
    tables = report_metrics.segments_by_variable(load_csv("reports/07_segmentos.csv"))
    if not tables:
        warn_missing("reports/07_segmentos.csv")
    for name, table in tables.items():
        st.markdown(f"*{name}*")
        st.dataframe(table, hide_index=True)

    if validation is not None:
        with st.expander("Informe completo de validación e interpretación (`reports/07_validacion.md`)"):
            st.markdown(documents.strip_title(validation))


def render_registry_tab() -> None:
    registro, ficha = st.tabs(["Registro del modelo (etapa 8)", "Ficha del modelo"])
    with registro:
        show_markdown("reports/08_registro.md")
    with ficha:
        show_markdown("models/ficha_modelo.md")


def render_decisions_tab() -> None:
    relative = "reports/decisiones_del_grupo.md"
    text = load_text(relative)
    if text is None:
        warn_missing(relative)
        return
    summary = documents.find_section(text, "Resumen", levels=(2,))
    intro, pending = documents.list_pending(text)
    if not pending:
        st.warning(f"No se encontró la sección B (pendientes de dato externo) en `{relative}`; se muestra el archivo completo.")
        st.markdown(documents.strip_title(text))
        return
    if summary is not None:
        st.info(summary.body)
    open_items = [p for p in pending if not p.closed]
    with st.container(border=True):
        st.subheader("B. Pendientes de dato externo")
        st.warning(f"**{len(open_items)} pendientes abiertos** y {len(pending) - len(open_items)} cerrados. "
                   "Dependen de datos o aprobaciones que el grupo no puede dar por sí solo.")
        if intro:
            st.markdown(intro)
        for item in pending:
            label = f"{item.title}" if item.closed else f"Abierto · {item.title}"
            with st.expander(label.replace("*", "")):
                st.markdown(item.body)
    for prefix, levels in (("Cómo leer", (2,)), ("A.", (2,)), ("C.", (2,))):
        section = documents.find_section(text, prefix, levels=levels)
        if section is not None:
            with st.expander(section.title):
                st.markdown(section.body)


# ---------- pestaña 8: el formulario de predicción (comportamiento sin cambios) ----------

@st.cache_resource
def get_model():
    return predict_module.load_model(MODEL_PATH)


@st.cache_data
def get_schema() -> dict:
    return schema_module.load_schema(SCHEMA_PATH)


def label(schema: dict, column: str) -> str:
    return schema.get("labels", {}).get(column, column)


def numeric_field(schema: dict, column: str, key: str):
    """Un campo numérico con su rango y mediana, y una casilla 'no sé' que deja el dato vacío."""
    low, high = schema.get("valid_range", {}).get(column) or schema["observed_range"][column]
    default = float(schema["median"][column])
    is_int = column in schema.get("integer_columns", [])
    if high <= low:
        high = low + 1
    default = min(max(default, low), high)
    unknown = st.checkbox(f"No sé: {label(schema, column)}", key=f"unk_{key}")
    if unknown:
        return np.nan
    if is_int:
        return st.number_input(label(schema, column), min_value=int(low), max_value=int(high), value=int(round(default)), step=1, key=key)
    return st.number_input(label(schema, column), min_value=float(low), max_value=float(high), value=float(default), key=key)


def build_form(schema: dict) -> dict:
    """Dibuja el formulario (tres columnas) y devuelve una fila de entrada."""
    row = {}
    columns = schema["numeric"] + schema["categorical"]
    cols = st.columns(3)
    for i, column in enumerate(columns):
        with cols[i % 3]:
            if column in schema["categorical"]:
                options = schema["categories"][column] + [UNKNOWN]
                choice = st.selectbox(label(schema, column), options, key=f"cat_{column}")
                row[column] = np.nan if choice == UNKNOWN else choice
            else:
                row[column] = numeric_field(schema, column, f"num_{column}")
    return row


def render_predict_tab(model, schema: dict) -> None:
    with st.form("entrada"):
        row = build_form(schema)
        submitted = st.form_submit_button("Evaluar", type="primary")

    if not submitted:
        st.info("Completa los datos y pulsa **Evaluar**. Marca *No sé* en lo que no conozcas.")
        return

    try:
        result = predict_module.predict_with_scores(pd.DataFrame([row]), model, schema)
    except predict_module.InputValidationError as error:
        st.error(f"Revisa los datos: {error}")
        return

    first = result.iloc[0]
    class_names = schema["class_names"]
    left, right = st.columns(2)
    with left:
        decision_labels = schema.get("decision_labels", {})
        st.metric("Resultado sugerido", decision_labels.get(str(first["decision"]), str(first["decision"])))
        detail = f"Clase más probable: **{first['most_likely']}**"
        if "expected_cost" in result.columns:
            detail += f" · costo esperado de esta decisión: **{first['expected_cost']:.2f}**"
        st.caption(detail)
        if bool(first["needs_review"]):
            st.warning("**Revisión recomendada:** el modelo duda, o la decisión de menor costo difiere de la clase más probable.")
        else:
            st.success("El modelo está seguro de este resultado.")
        for message in result.attrs.get("warnings", []):
            st.warning(message)
    with right:
        st.write("**Probabilidad por clase**")
        st.bar_chart(pd.DataFrame({"probabilidad": [first[f"proba_{c}"] for c in class_names]}, index=class_names))

    if "cost_matrix" in schema:
        with st.expander("¿Cómo se decide? (matriz de costos)"):
            st.markdown("La decisión es la de **menor costo esperado**, no necesariamente la más probable.")
            st.dataframe(pd.DataFrame(schema["cost_matrix"], index=[f"real {c}" for c in class_names], columns=[f"decide {c}" for c in class_names]))
    with st.expander("Uso responsable"):
        st.markdown(schema.get("responsible_use", DEFAULT_RESPONSIBLE_USE))


def main() -> None:
    st.set_page_config(page_title="Venta cruzada de seguros", page_icon="🧭", layout="wide")

    model_ready = MODEL_PATH.exists() and SCHEMA_PATH.exists()
    schema = get_schema() if model_ready else {}
    st.title(schema.get("app_title", DEFAULT_TITLE))
    st.caption("Herramienta de apoyo a la decisión. **No decide por sí sola.**")

    render_notices()

    tabs = st.tabs(TAB_TITLES)
    with tabs[0]:
        show_markdown("reports/00_caso.md")
    with tabs[1]:
        show_markdown("reports/01_eda.md")
    with tabs[2]:
        render_features_tab()
    with tabs[3]:
        render_models_tab()
    with tabs[4]:
        render_results_tab()
    with tabs[5]:
        render_registry_tab()
    with tabs[6]:
        render_decisions_tab()
    with tabs[7]:
        if model_ready:
            render_predict_tab(get_model(), schema)
        else:
            st.error(
                "Falta `models/model.joblib` o `models/input_schema.json`. "
                "Ejecuta el notebook `notebooks/09_inferencia.ipynb` para generarlos."
            )


if __name__ == "__main__":  # `streamlit run` ejecuta el archivo como programa principal
    main()
