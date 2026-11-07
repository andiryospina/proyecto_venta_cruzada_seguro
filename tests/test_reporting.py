"""Pruebas de `proyecto.reporting`: leer informes, partir markdown y armar tarjetas desde el JSON de la prueba.

Las primeras usan datos de juguete; las últimas (`real_*`) comprueban que los informes reales del repositorio siguen
teniendo las secciones que la app necesita (si alguien cambia un título, falla aquí y no en la nube).
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from proyecto.reporting.documents import (
    find_section,
    list_pending,
    pick_bullets,
    read_csv,
    read_json,
    read_text,
    split_sections,
    strip_title,
)
from proyecto.reporting.metrics import (
    build_metric_cards,
    format_number,
    format_percent,
    segments_by_variable,
    sensitivity_rows,
)

ROOT = Path(__file__).resolve().parents[1]

MARKDOWN = """# Título

Introducción.

## Uno

Texto uno.

### Uno punto uno

Detalle.

```
# no es un encabezado
```

## Dos

Texto dos.
"""


# ---------- documents ----------

def test_read_helpers_return_none_when_the_file_is_missing(tmp_path):
    assert read_text(tmp_path / "no_existe.md") is None
    assert read_json(tmp_path / "no_existe.json") is None
    assert read_csv(tmp_path / "no_existe.csv") is None


def test_read_helpers_read_existing_files(tmp_path):
    (tmp_path / "a.md").write_text("hola ñ", encoding="utf-8")
    (tmp_path / "a.json").write_text('{"x": 1}', encoding="utf-8")
    (tmp_path / "a.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    assert read_text(tmp_path / "a.md") == "hola ñ"
    assert read_json(tmp_path / "a.json") == {"x": 1}
    assert list(read_csv(tmp_path / "a.csv").columns) == ["a", "b"]


def test_read_json_returns_none_for_invalid_json(tmp_path):
    (tmp_path / "mal.json").write_text("{no es json", encoding="utf-8")
    assert read_json(tmp_path / "mal.json") is None


def test_split_sections_by_level_ignores_headings_inside_code():
    sections = split_sections(MARKDOWN, 2)
    assert [s.title for s in sections] == ["Uno", "Dos"]
    assert "Uno punto uno" in sections[0].body          # la subsección va dentro de su sección
    assert "# no es un encabezado" in sections[0].body  # y el bloque de código no parte nada
    assert "Texto dos" not in sections[0].body


def test_find_section_by_prefix_includes_subsections_and_returns_none_if_absent():
    section = find_section(MARKDOWN, "uno")
    assert section is not None and section.level == 2 and "Detalle." in section.body
    sub = find_section(MARKDOWN, "Uno punto")
    assert sub is not None and sub.level == 3 and sub.body.strip().startswith("Detalle.")
    assert find_section(MARKDOWN, "Tres") is None
    assert find_section("", "Uno") is None


def test_strip_title_removes_only_the_first_h1():
    assert strip_title(MARKDOWN).startswith("Introducción.")
    assert strip_title("Sin título\n\ntexto") == "Sin título\n\ntexto"
    assert strip_title("") == ""


def test_pick_bullets_matches_the_start_even_with_bold_and_wrapped_lines():
    markdown = (
        "- **Datos:** uno\n"
        "- **Atributos sensibles:** usa edad\n"
        "  y género en dos líneas.\n"
        "- Otra cosa\n"
    )
    picked = pick_bullets(markdown, ["Atributos sensibles"])
    assert len(picked) == 1 and "género en dos líneas" in picked[0]
    assert pick_bullets(markdown, ["No existe"]) == []


PENDING_MD = """# Registro

## A. Decisiones

tabla

## B. Pendientes de dato externo

> Nota de la sección.

### P01 · Valor de R

| | |
|---|---|
| **Qué falta** | El margen |

### P12 · ¿Por qué? — **[CERRADO 2026-11-06]**

Se resolvió.

## C. Hoja
"""


def test_list_pending_splits_items_and_flags_the_closed_ones():
    intro, items = list_pending(PENDING_MD)
    assert "Nota de la sección." in intro
    assert [p.code for p in items] == ["P01", "P12"]
    assert [p.closed for p in items] == [False, True]
    assert "El margen" in items[0].body
    assert "Hoja" not in items[1].body                  # no se sale de la sección B


def test_list_pending_without_section_b_returns_empty():
    assert list_pending("# Nada\n\n## A. Algo\n") == ("", [])


# ---------- metrics ----------

def test_format_number_and_percent_use_spanish_separators():
    assert format_number(0.33122982865839257, 4) == "0,3312"
    assert format_number(76222, 0) == "76.222"
    assert format_number(-0.0408, 4) == "-0,0408"
    assert format_percent(0.3649996, 1) == "36,5 %"


METRICS = {
    "prueba": {
        "clientes": 1000,
        "modelo": {"cost": 0.30, "cost_ic95": [0.28, 0.32], "contact_rate": 0.4, "recall": 0.9, "precision": 0.25,
                   "pr_auc": 0.35, "roc_auc": 0.85, "capture_20": 0.55},
        "linea_base": {"cost": 0.37},
        "diferencia_costo": {"valor": -0.07, "ic95": [-0.09, -0.05]},
        "sensibilidad": {"10_a_1": {"modelo": 0.40, "linea_base": 0.38}, "3_a_1": {"modelo": 0.30, "linea_base": 0.36}},
    }
}


def test_build_metric_cards_takes_every_number_from_the_json():
    cards = {c.label: c for c in build_metric_cards(METRICS)}
    assert cards["Costo por cliente"].value == "0,3000"
    assert "0,2800" in cards["Costo por cliente"].help and "0,3200" in cards["Costo por cliente"].help
    assert cards["Diferencia frente a la regla de negocio"].value == "-0,0700"
    assert cards["% de la base a llamar"].value == "40,0 %"
    assert cards["Recall"].value == "90,0 %"
    assert cards["PR-AUC"].value == "0,350"
    assert len(cards) == 9


def test_build_metric_cards_skips_what_is_missing_and_never_invents_zeros():
    partial = {"prueba": {"modelo": {"cost": 0.3}}}
    labels = [c.label for c in build_metric_cards(partial)]
    assert labels == ["Costo por cliente"]
    assert build_metric_cards({}) == []
    assert build_metric_cards(None) == []


def test_sensitivity_rows_sorted_by_r_and_say_who_wins():
    rows = sensitivity_rows(METRICS)
    assert [r["R"] for r in rows] == ["R = 3", "R = 10"]
    assert [r["Mejor"] for r in rows] == ["Modelo", "Regla de negocio"]
    assert rows[0]["Costo del modelo"] == "0,3000"
    assert sensitivity_rows({}) == []


def test_segments_by_variable_groups_and_formats():
    df = pd.DataFrame({
        "variable": ["Gender", "Gender", "Age"],
        "segment": ["Male", "Female", "18-29"],
        "clients": [41309, 34913, 31037],
        "cost": [0.367, 0.289, 0.168],
        "contact_rate": [0.42, 0.30, 0.08],
        "positive_rate": [0.14, 0.10, 0.04],
        "gap_contact_vs_real": [0.28, 0.20, 0.04],
        "recall": [0.90, 0.85, 0.48],
    })
    tables = segments_by_variable(df)
    assert set(tables) == {"Género", "Edad"}
    male = tables["Género"].iloc[0]
    assert male["Segmento"] == "Male" and male["Clientes"] == "41.309" and male["Recall"] == "90,0 %"
    assert segments_by_variable(None) == {}
    assert segments_by_variable(pd.DataFrame({"a": [1]})) == {}


# ---------- contra los archivos reales del repositorio ----------

def test_real_validation_report_has_the_double_opening_section():
    text = read_text(ROOT / "reports" / "07_validacion.md")
    section = find_section(text, "3.1")
    assert section is not None and "dos veces" in section.title + section.body


def test_real_model_card_has_the_sensitive_and_test_bullets():
    text = read_text(ROOT / "models" / "ficha_modelo.md")
    limits = find_section(text, "Límites")
    assert limits is not None
    bullets = pick_bullets(limits.body, ["Atributos sensibles", "La prueba en el grupo"])
    assert len(bullets) == 2 and "Gender" in bullets[0]


def test_real_decisions_file_lists_the_pending_items():
    intro, items = list_pending(read_text(ROOT / "reports" / "decisiones_del_grupo.md"))
    codes = [p.code for p in items]
    assert sorted(codes) == [f"P{n:02d}" for n in range(1, 13)]
    assert sum(not p.closed for p in items) >= 1


def test_real_test_metrics_make_all_cards_and_match_the_json():
    metrics = json.loads((ROOT / "reports" / "07_metricas_test.json").read_text(encoding="utf-8"))
    cards = {c.label: c for c in build_metric_cards(metrics)}
    assert len(cards) == 9
    assert cards["Costo por cliente"].value == format_number(metrics["prueba"]["modelo"]["cost"], 4)
    assert sensitivity_rows(metrics)


def test_real_segments_file_has_gender_age_and_region():
    tables = segments_by_variable(read_csv(ROOT / "reports" / "07_segmentos.csv"))
    assert {"Género", "Edad", "Región"} <= set(tables)


@pytest.mark.parametrize("relative", [
    "reports/00_caso.md", "reports/01_eda.md", "reports/04_features.md", "reports/05_torneo.md", "reports/06_optimizacion.md",
    "reports/07_validacion.md", "reports/08_registro.md", "models/ficha_modelo.md", "reports/decisiones_del_grupo.md",
    "reports/prueba_abierta.txt", "reports/07_calibracion.png", "reports/07_shap.png",
])
def test_real_files_the_app_reads_exist(relative):
    assert (ROOT / relative).is_file()


# --- portada de la app: cifras y umbral (specs/008, mejora visual)
def test_hero_stats_come_from_the_json_and_skip_what_is_missing():
    from proyecto.reporting.metrics import hero_stats

    metrics = {"prueba": {"modelo": {"contact_rate": 0.365, "recall": 0.879, "cost": 0.3312}, "linea_base": {"cost": 0.3720}}}
    assert hero_stats(metrics) == [("36,5 %", "de la lista a llamar"), ("87,9 %", "de los interesados encontrados"),
                                   ("−11 %", "de costo frente a la mejor regla")]
    assert hero_stats({"prueba": {"modelo": {"recall": 0.879}}}) == [("87,9 %", "de los interesados encontrados")]
    assert hero_stats(None) == [] and hero_stats({}) == []


def test_hero_stats_never_show_a_saving_when_the_model_is_not_cheaper():
    from proyecto.reporting.metrics import hero_stats

    worse = {"prueba": {"modelo": {"cost": 0.40}, "linea_base": {"cost": 0.37}}}
    assert hero_stats(worse) == []


def test_decision_threshold_is_derived_from_the_cost_matrix():
    from proyecto.reporting.metrics import decision_threshold

    assert decision_threshold([[0, 1], [5, 0]]) == pytest.approx(1 / 6)
    assert decision_threshold([[0, 1], [10, 0]]) == pytest.approx(1 / 11)
    assert decision_threshold(None) is None and decision_threshold([[0, 0], [0, 0]]) is None and decision_threshold("no") is None
