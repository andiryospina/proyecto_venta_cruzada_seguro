# Especificación: Variables nuevas (`002-variables`)

**Fecha:** 2026-10-31 · **Estado:** aprobado por el grupo (2026-10-31)
**Entrada:** `reports/01_eda.md` (sección "Relación de cada variable con la respuesta") · Ejemplo del curso:
`material-del-curso/ejemplo-creditsight/src/creditsight/features/engineering.py`

## Qué se quiere

Crear `src/proyecto/features/engineering.py` siguiendo el ejemplo del curso. Debe hacer tres cosas:
- `add_features(df)` agrega las variables nuevas.
- `feature_columns(...)` decide qué columnas usa el modelo, con interruptores para medir cada grupo con y sin él.
- `build_preprocessor` (ya existe en `preprocessing.py`) recibe esas columnas.

## Variables nuevas

Todas se calculan **fila por fila**, con datos que se conocen **antes** de llamar al cliente. No aprenden nada de los datos y por eso no hay fuga. Las cifras se midieron en `data/processed/train.parquet` (304.238 filas); la prueba sigue cerrada.

| Variable | Cálculo | Por qué podría ayudar | Evidencia |
|---|---|---|---|
| `uninsured_with_damage` | 1 si `Previously_Insured == 0` y `Vehicle_Damage == 1` | Es la interacción clave del EDA (también es la regla de la línea base) | Tasa 25,0 % frente a 0,5 % |
| `damage_x_vehicle_age` | `Vehicle_Damage × Vehicle_Age` (0–2) | Un vehículo más viejo con daño previo se interesa más | AUC 0,760 |
| `is_young_customer` | 1 si `Age < 30` | De 20 a 30 años casi nadie se interesa | Tasa 4,1 % frente a 17,9 % |
| `age_peak_distance` | `abs(Age − 42)` | La edad tiene forma de campana (máximo entre 35 y 50); un modelo lineal no la capta con `Age` sola | AUC 0,671 frente a 0,627 de `Age` |
| `premium_per_age` | `Annual_Premium / Age` (vacío si la edad falta o es ≤ 0) | Prima relativa a la etapa de vida | AUC 0,577 frente a 0,530 de la prima |

Se descartan antes de medir en el modelo: `vintage_months` (AUC 0,501, sin señal) e `insured_with_damage` (2,6 % de clientes, redundante).

Los umbrales 30 y 42 salen del EDA, que se calculó sobre la porción de exploración (= entrenamiento), no sobre la prueba.

## Interruptores (`feature_columns`)

- `use_engineered` (por defecto `False`, como en el ejemplo): suma las 5 variables nuevas. Solo entran al modelo final si la etapa 04 demuestra que mejoran más que el ruido entre pliegues.
- `use_gender` (por defecto `True`): permite medir sin `Gender` (decisión 10 del EDA, equidad).

## Requisitos

- RF-01 `add_features` no modifica el original y no borra filas.
- RF-02 División segura: si el denominador es 0 o vacío, el resultado es vacío (nunca infinito).
- RF-03 `build_preprocessor(use_engineered=..., use_gender=...)` arma las columnas a partir de `feature_columns`; sin argumentos se comporta como hoy.
- RF-04 Cada variable y cada interruptor tienen su prueba en `tests/test_features.py`.
