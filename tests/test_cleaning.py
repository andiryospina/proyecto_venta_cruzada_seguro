"""Pruebas de la limpieza (especificaciones/03-preprocesamiento.md, sección 3). Datos hechos a mano."""
import pandas as pd
import pytest

from proyecto.config import DROPPED_COLUMNS, ID_COL, RAW_COLUMNS
from proyecto.data.cleaning import (
    add_min_premium_flag,
    cast_codes_to_int,
    clean,
    drop_excluded_columns,
    encode_categoricals,
    flag_impossible_values,
    load_raw,
)


def raw_rows() -> pd.DataFrame:
    """Tres clientes como llegan en el CSV crudo."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "Gender": ["Male", "Female", "Male"],
        "Age": [44, 21, 76],
        "Driving_License": [1, 1, 0],
        "Region_Code": [28.0, 3.0, 11.0],
        "Previously_Insured": [0, 1, 0],
        "Vehicle_Age": ["> 2 Years", "< 1 Year", "1-2 Year"],
        "Vehicle_Damage": ["Yes", "No", "Yes"],
        "Annual_Premium": [40454.0, 2630.0, 540165.0],
        "Policy_Sales_Channel": [26.0, 152.0, 160.0],
        "Vintage": [217, 27, 10],
        "Response": [1, 0, 0],
    })


# --- load_raw -------------------------------------------------------------------------------------

def test_load_raw_reads_expected_columns(tmp_path):
    path = tmp_path / "dataset.csv"
    raw_rows().to_csv(path, index=False)
    df = load_raw(path)
    assert list(df.columns) == RAW_COLUMNS
    assert len(df) == 3


def test_load_raw_rejects_unexpected_columns(tmp_path):
    path = tmp_path / "dataset.csv"
    raw_rows().assign(Name="Ana").to_csv(path, index=False)
    with pytest.raises(ValueError, match="Columnas inesperadas"):
        load_raw(path)


def test_no_personal_columns(tmp_path):
    """Cargar y limpiar solo deja las columnas esperadas (ninguna con datos personales)."""
    path = tmp_path / "dataset.csv"
    raw_rows().to_csv(path, index=False)
    out = clean(load_raw(path))
    assert set(out.columns) == (set(RAW_COLUMNS) - set(DROPPED_COLUMNS)) | {"is_min_premium"}


# --- drop_excluded_columns ------------------------------------------------------------------------

def test_drop_excluded_columns():
    """Policy_Sales_Channel (canal de contacto, posible fuga) no sale de la limpieza."""
    out = drop_excluded_columns(raw_rows())
    assert "Policy_Sales_Channel" not in out.columns
    assert len(out.columns) == len(RAW_COLUMNS) - 1


def test_clean_removes_channel():
    assert "Policy_Sales_Channel" not in clean(raw_rows()).columns


# --- cast_codes_to_int ----------------------------------------------------------------------------

def test_cast_codes_to_int():
    out = cast_codes_to_int(raw_rows())
    assert out["Region_Code"].tolist() == [28, 3, 11]
    assert str(out["Region_Code"].dtype) == "Int64"


def test_cast_codes_rejects_fraction():
    dirty = raw_rows()
    dirty.loc[0, "Region_Code"] = 28.5
    with pytest.raises(ValueError, match="Region_Code"):
        cast_codes_to_int(dirty)


# --- encode_categoricals --------------------------------------------------------------------------

def test_encode_categoricals():
    out = encode_categoricals(raw_rows())
    assert out["Gender"].tolist() == [1, 0, 1]
    assert out["Vehicle_Damage"].tolist() == [1, 0, 1]
    assert out["Vehicle_Age"].tolist() == [2, 0, 1]


def test_encode_rejects_unknown():
    dirty = raw_rows()
    dirty.loc[1, "Vehicle_Age"] = "3 Years"
    with pytest.raises(ValueError, match="Vehicle_Age"):
        encode_categoricals(dirty)


# --- add_min_premium_flag -------------------------------------------------------------------------

def test_add_min_premium_flag():
    out = add_min_premium_flag(raw_rows())
    assert out["is_min_premium"].tolist() == [0, 1, 0]
    assert out["Annual_Premium"].tolist() == [40454.0, 2630.0, 540165.0]   # el valor se conserva


# --- flag_impossible_values -----------------------------------------------------------------------

def test_flag_impossible_values():
    dirty = raw_rows()
    dirty["Age"] = [44, 5, 130]                 # 5 y 130 años son imposibles
    dirty["Annual_Premium"] = [40454.0, -10.0, 0.0]
    dirty["Vintage"] = [217, -1, 10]
    dirty["Driving_License"] = [1, 2, 0]        # 2 no es binario
    out = flag_impossible_values(dirty)
    assert out["Age"].isna().tolist() == [False, True, True]
    assert out["Annual_Premium"].isna().tolist() == [False, True, True]
    assert out["Vintage"].isna().tolist() == [False, True, False]
    assert out["Driving_License"].isna().tolist() == [False, True, False]
    assert len(out) == 3                         # no se borran filas


def test_flag_impossible_values_keeps_limits():
    """Los límites del rango son válidos: 18 y 100 años, antigüedad 0, prima mínima 2.630."""
    edge = raw_rows()
    edge["Age"] = [18, 100, 50]
    edge["Vintage"] = [0, 10, 299]
    out = flag_impossible_values(edge)
    assert out[["Age", "Vintage", "Annual_Premium"]].notna().all().all()


def test_add_min_premium_flag_only_exact_value():
    """Solo la prima exactamente 2.630 se marca; 2.630,5 o un vacío no."""
    dirty = raw_rows()
    dirty["Annual_Premium"] = [2630.5, float("nan"), 2630.0]
    assert add_min_premium_flag(dirty)["is_min_premium"].tolist() == [0, 0, 1]


def test_clean_with_missing_inputs():
    """Si llegan vacíos en el crudo, clean() los conserva como vacíos sin fallar ni borrar filas."""
    dirty = raw_rows()
    dirty["Age"] = dirty["Age"].astype(float)
    dirty.loc[0, "Age"] = float("nan")
    dirty.loc[1, "Region_Code"] = float("nan")
    out = clean(dirty)
    assert len(out) == 3
    assert out["Age"].isna().tolist() == [True, False, False]
    assert out["Region_Code"].isna().tolist() == [False, True, False]


def test_flag_impossible_values_keeps_high_premium():
    """La prima alta es real (decisión de negocio): no se marca como vacía."""
    out = flag_impossible_values(raw_rows())
    assert out["Annual_Premium"].notna().all()


# --- clean ----------------------------------------------------------------------------------------

def test_clean_keeps_rows():
    raw = raw_rows()
    out = clean(raw)
    assert len(out) == len(raw)
    assert out[ID_COL].tolist() == raw[ID_COL].tolist()


def test_clean_leaves_no_text_columns():
    out = clean(raw_rows())
    assert all(pd.api.types.is_numeric_dtype(out[c]) for c in out.columns)


def test_clean_does_not_modify_input():
    raw = raw_rows()
    before = raw.copy()
    clean(raw)
    pd.testing.assert_frame_equal(raw, before)
