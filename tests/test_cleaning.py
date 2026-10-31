"""Pruebas de la limpieza: una por regla, con un caso normal y uno sucio hecho a mano (no usan data/raw)."""
import pandas as pd
import pytest

from proyecto.data.cleaning import (
    EXPECTED_COLUMNS,
    cast_code_columns,
    clean,
    drop_personal_columns,
    encode_vehicle_age,
    encode_vehicle_damage,
    find_impossible_values,
    find_test_csv,
    find_train_csv,
    flag_minimum_premium,
)


def make_rows(**overrides) -> pd.DataFrame:
    """Dos clientes válidos; `overrides` reemplaza columnas completas para fabricar casos sucios."""
    data = {
        "id": [1, 2], "Gender": ["Male", "Female"], "Age": [44, 29], "Driving_License": [1, 1],
        "Region_Code": [28.0, 3.0], "Previously_Insured": [0, 1], "Vehicle_Age": ["> 2 Years", "< 1 Year"],
        "Vehicle_Damage": ["Yes", "No"], "Annual_Premium": [40454.0, 2630.0], "Policy_Sales_Channel": [26.0, 152.0],
        "Vintage": [217, 10], "Response": [1, 0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


# Regla 3 · Vehicle_Damage Yes/No -> 1/0
def test_vehicle_damage_is_converted_to_binary():
    out = encode_vehicle_damage(make_rows())
    assert out["Vehicle_Damage"].tolist() == [1, 0]


def test_vehicle_damage_rejects_unknown_value():
    with pytest.raises(ValueError, match="desconocidos"):
        encode_vehicle_damage(make_rows(Vehicle_Damage=["Yes", "Maybe"]))


def test_vehicle_damage_rejects_missing_value():
    with pytest.raises(ValueError, match="vacíos"):
        encode_vehicle_damage(make_rows(Vehicle_Damage=["Yes", None]))


# Regla 3 · Vehicle_Age conserva el orden 0-1-2
def test_vehicle_age_keeps_natural_order():
    rows = make_rows(id=[1, 2, 3], Gender=["a", "b", "c"], Age=[30, 30, 30], Driving_License=[1, 1, 1],
                     Region_Code=[1.0, 1.0, 1.0], Previously_Insured=[0, 0, 0],
                     Vehicle_Age=["< 1 Year", "1-2 Year", "> 2 Years"], Vehicle_Damage=["Yes"] * 3,
                     Annual_Premium=[1.0] * 3, Policy_Sales_Channel=[1.0] * 3, Vintage=[1, 1, 1], Response=[0, 0, 0])
    assert encode_vehicle_age(rows)["Vehicle_Age"].tolist() == [0, 1, 2]


def test_vehicle_age_rejects_unknown_value():
    with pytest.raises(ValueError, match="desconocidos"):
        encode_vehicle_age(make_rows(Vehicle_Age=["> 2 Years", "3 Years"]))


# Regla 5 · códigos de región y canal pasan a entero
def test_code_columns_become_integers():
    out = cast_code_columns(make_rows())
    assert out["Region_Code"].tolist() == [28, 3]
    assert str(out["Region_Code"].dtype) == "int64"
    assert str(out["Policy_Sales_Channel"].dtype) == "int64"


def test_code_columns_reject_missing_or_fractional_codes():
    with pytest.raises(ValueError, match="vacíos"):
        cast_code_columns(make_rows(Region_Code=[28.0, None]))
    with pytest.raises(ValueError, match="no enteros"):
        cast_code_columns(make_rows(Region_Code=[28.5, 3.0]))


# Regla 4 · marca de la prima mínima (se marca, no se cambia)
def test_minimum_premium_is_flagged_not_changed():
    rows = make_rows()
    out = flag_minimum_premium(rows)
    assert out["Premium_is_minimum"].tolist() == [0, 1]
    assert out["Annual_Premium"].tolist() == rows["Annual_Premium"].tolist()


# Valores imposibles: se detectan y se cuentan
def test_no_impossible_values_in_normal_rows():
    assert find_impossible_values(make_rows()) == {}


def test_impossible_values_are_counted():
    problems = find_impossible_values(make_rows(Age=[150, 29], Previously_Insured=[0, 2], Vintage=[-1, 10]))
    assert problems == {"Age fuera de rango": 1, "Previously_Insured distinto de 0/1": 1, "Vintage negativo": 1}


# Datos personales: ninguna columna personal sobrevive
def test_no_personal_columns():
    rows = make_rows().assign(nombre=["Ana", "Luis"], documento=["1", "2"])
    out = drop_personal_columns(rows, columns=("nombre", "documento"))
    assert not {"nombre", "documento"} & set(out.columns)


# Función completa
def test_clean_is_complete_and_does_not_modify_input():
    rows = make_rows()
    before = rows.copy(deep=True)
    out = clean(rows)
    pd.testing.assert_frame_equal(rows, before)          # no toca el original
    assert len(out) == len(rows)                          # no pierde filas
    assert out["Vehicle_Damage"].tolist() == [1, 0]
    assert out["Vehicle_Age"].tolist() == [2, 0]
    assert out["Premium_is_minimum"].tolist() == [0, 1]
    assert out["Response"].tolist() == [1, 0]             # el objetivo no se altera


def test_clean_works_without_target_column():
    out = clean(make_rows().drop(columns="Response"))
    assert "Response" not in out.columns
    assert set(EXPECTED_COLUMNS) <= set(out.columns)


def test_clean_rejects_missing_columns():
    with pytest.raises(ValueError, match="Faltan columnas"):
        clean(make_rows().drop(columns="Age"))


def test_clean_rejects_impossible_values():
    with pytest.raises(ValueError, match="imposibles"):
        clean(make_rows(Age=[150, 29]))


# Ubicación del CSV: la plantilla del curso y el repo con un único dataset.csv deben funcionar
def test_find_train_csv_prefers_course_layout(tmp_path):
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "train.csv").write_text("id")
    (tmp_path / "dataset.csv").write_text("id")
    assert find_train_csv(tmp_path) == tmp_path / "data" / "raw" / "train.csv"


def test_find_train_csv_falls_back_to_dataset_csv_in_root(tmp_path):
    (tmp_path / "dataset.csv").write_text("id")
    assert find_train_csv(tmp_path) == tmp_path / "dataset.csv"


def test_find_train_csv_fails_with_a_clear_message(tmp_path):
    with pytest.raises(FileNotFoundError, match="dataset.csv"):
        find_train_csv(tmp_path)


def test_find_test_csv_is_optional(tmp_path):
    assert find_test_csv(tmp_path) is None
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "test.csv").write_text("id")
    assert find_test_csv(tmp_path) == tmp_path / "data" / "raw" / "test.csv"
