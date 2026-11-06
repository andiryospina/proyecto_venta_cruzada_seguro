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
