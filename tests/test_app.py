"""Prueba de humo de la app de Streamlit con el modelo real del repositorio (el mismo que se despliega)."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"
needs_files = pytest.mark.skipif(not (ROOT / "models" / "model.joblib").exists() or not (ROOT / "models" / "input_schema.json").exists(),
                                 reason="falta models/model.joblib o models/input_schema.json (se generan en el notebook 09)")


@needs_files
def test_app_loads_with_the_real_model_and_shows_the_form():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    labels = [w.label for w in at.number_input] + [w.label for w in at.selectbox]
    assert len(labels) >= 7                      # los datos que pide el formulario salen del esquema
    assert any("daños" in label for label in labels)


@needs_files
def test_app_answers_with_a_decision_for_the_default_values():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error
    assert at.metric[0].label == "Resultado sugerido"
    assert at.metric[0].value in {"LLAMAR", "NO LLAMAR"}


@needs_files
def test_app_decision_changes_with_the_key_variables():
    """Con seguro previo y sin daño no se llama; con daño y sin seguro previo, sí: la app usa de verdad el modelo."""
    def decide(insured, damage):
        at = AppTest.from_file(str(APP), default_timeout=90).run()
        for box in at.selectbox:
            if "seguro de vehículo" in box.label:
                box.set_value(insured)
            if "daños" in box.label:
                box.set_value(damage)
        at.button[0].click().run()
        assert not at.exception, [e.value for e in at.exception]
        return at.metric[0].value

    assert decide("Yes", "No") == "NO LLAMAR"
    assert decide("No", "Yes") == "LLAMAR"


# ---------------------------------------------------------------------------------------------------------------
# Pestañas que cuentan el proyecto (specs/008-app-streamlit). Las tres pruebas de arriba no cambian.
# ---------------------------------------------------------------------------------------------------------------
import json  # noqa: E402
import shutil  # noqa: E402

TAB_TITLES = ["Caso de negocio", "Datos y EDA", "Variables", "Modelos", "Resultado en la prueba", "Registro y ficha",
              "Decisiones y pendientes", "Probar el modelo"]


def _top_tabs(at):
    """Las 8 pestañas principales (las subpestañas no llevan número delante)."""
    return [t for t in at.tabs if t.label[:1].isdigit() and " · " in t.label]


def _markdown_text(block) -> str:
    return "\n".join(str(m.value) for m in block.markdown)


def test_app_has_the_eight_tabs_in_order_and_none_fails():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    labels = [t.label for t in _top_tabs(at)]
    assert len(labels) == 8
    for expected, label in zip(TAB_TITLES, labels):
        assert expected in label


def test_report_tabs_show_content_from_their_files():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error                                                  # ningún archivo faltante en el repositorio
    top = _top_tabs(at)
    for index in (0, 1, 2, 3, 4, 5, 6):                                  # cada pestaña con informe tiene texto largo
        assert len(_markdown_text(top[index])) > 500, TAB_TITLES[index]
    assert "Informe del EDA" not in _markdown_text(top[1])               # el título del archivo lo pone la pestaña, no se repite
    assert len(top[7].number_input) + len(top[7].selectbox) >= 7         # el formulario vive en la última pestaña


def test_results_tab_cards_match_the_metrics_json():
    metrics = json.loads((ROOT / "reports" / "07_metricas_test.json").read_text(encoding="utf-8"))
    from proyecto.reporting.metrics import format_number, format_percent

    at = AppTest.from_file(str(APP), default_timeout=90).run()
    text = _markdown_text(_top_tabs(at)[4])
    model = metrics["prueba"]["modelo"]
    assert f"## {format_number(model['cost'], 4)}" in text
    assert f"## {format_percent(model['recall'])}" in text
    assert f"## {format_number(metrics['prueba']['diferencia_costo']['valor'], 4)}" in text
    assert len(_top_tabs(at)[4].dataframe) >= 4                                # sensibilidad + segmentos (género, edad, región)


def test_honesty_notices_are_visible_above_the_tabs_and_come_from_the_files():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    ficha = (ROOT / "models" / "ficha_modelo.md").read_text(encoding="utf-8")
    warnings = " ".join(str(w.value) for w in at.warning)
    assert "Atributos sensibles" in warnings and "La prueba en el grupo" in warnings
    assert "Atributos sensibles" in ficha                                # el texto sale de la ficha, no está reescrito
    assert any("pendientes de terceros" in str(i.value) for i in at.info)
    assert "dos veces" in " ".join(str(w.value) for w in _top_tabs(at)[4].warning)                     # la sección 3.1 destacada en la pestaña de resultados


def test_decisions_tab_highlights_the_pending_section_first():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    tab = _top_tabs(at)[6]
    assert any("pendientes abiertos" in str(w.value) for w in tab.warning)
    labels = [e.label for e in tab.expander]
    assert sum(label.startswith(("Abierto", "P")) or "· " in label for label in labels) >= 12   # P01 a P12


def test_predict_form_still_answers_inside_the_last_tab():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert _top_tabs(at)[7].metric[0].value in {"LLAMAR", "NO LLAMAR"}


def test_missing_reports_show_a_warning_and_the_app_keeps_working(tmp_path):
    """Copia mínima del repositorio sin `reports/`: las pestañas avisan, no fallan, y el formulario sigue funcionando."""
    (tmp_path / "app").mkdir()
    shutil.copy(APP, tmp_path / "app" / "streamlit_app.py")
    shutil.copytree(ROOT / "src", tmp_path / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "models", tmp_path / "models", ignore=shutil.ignore_patterns("ficha_modelo.md"))
    at = AppTest.from_file(str(tmp_path / "app" / "streamlit_app.py"), default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("reports/00_caso.md" in str(w.value) for w in _top_tabs(at)[0].warning)
    assert any("models/ficha_modelo.md" in str(w.value) for w in at.warning)
    at.button[0].click().run()
    assert _top_tabs(at)[7].metric[0].value in {"LLAMAR", "NO LLAMAR"}
