# Informe del EDA

> **BORRADOR.** Primera medición hecha sobre `data/raw/train.csv`. El grupo debe reproducir estas cifras en
> `notebooks/02_eda.ipynb` antes de darlo por cerrado. Cada decisión se implementa luego en `src/proyecto/data/` con pruebas.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`.

## Qué son los datos

- **Filas × columnas:** 381.109 × 12 en `train.csv`; 127.037 × 11 en `test.csv` (no trae `Response`).
- **Unidad de análisis (qué es una fila):** un cliente con seguro de salud y su respuesta a la oferta de seguro de vehículo.
- **¿Una entidad aparece en varias filas?** No. `id` es único (1 a 381.109 en train; 381.110 a 508.146 en test) y no hay filas duplicadas.
- **Objetivo y distribución:** `Response`: 87,74 % de 0 y 12,26 % de 1.
- **Línea base (resultado de una regla trivial):** "siempre 0" acierta el 87,7 % y no encuentra a ningún comprador. Contactar solo a quien tiene
  `Vehicle_Damage = Yes` capta al 23,8 % de ese grupo frente a 0,5 % del otro.

### Diccionario de variables

| Variable | Tipo | Qué es | Observación medida |
|---|---|---|---|
| `id` | entero | Identificador del cliente | Único; no es predictor |
| `Gender` | texto | Género | Male 54 % / Female 46 %; aceptan 13,8 % y 10,4 % |
| `Age` | entero | Edad | 20 a 85, mediana 36; la aceptación sube y luego baja (ver Calidad) |
| `Driving_License` | 0/1 | Tiene licencia | 812 filas con 0 (0,2 %); casi constante |
| `Region_Code` | decimal | Código de región | 53 valores; aceptación entre 4,1 % y 19,2 % |
| `Previously_Insured` | 0/1 | Ya tiene seguro de vehículo | Acepta 22,5 % de quienes no, 0,1 % de quienes sí |
| `Vehicle_Age` | texto | Antigüedad del vehículo | `< 1 Year` 4,4 %; `1-2 Year` 17,4 %; `> 2 Years` 29,4 % |
| `Vehicle_Damage` | texto | Vehículo con daño previo | Yes 23,8 % / No 0,5 % |
| `Annual_Premium` | decimal | Prima anual | Mín. 2.630, mediana 31.669, máx. 540.165 |
| `Policy_Sales_Channel` | decimal | Código del canal de venta | 155 valores; 3 canales concentran el 76 % de las filas |
| `Vintage` | entero | Días como cliente | 10 a 299; aceptación 12,3 % en cada tercio |
| `Response` | 0/1 | Objetivo | 12,26 % de 1 |

## Calidad de los datos

- **Sin vacíos:** 0 nulos en todas las columnas de `train.csv`.
- **Valor centinela probable:** el 17 % de las filas tiene `Annual_Premium` = 2.630, que es además el mínimo. Su aceptación (13,1 %) es parecida a la del resto (12,1 %).
- **Valores extremos:** 778 filas (0,2 %) superan 100.000 de prima, con un máximo de 540.165 frente a un percentil 99 de 72.963.
- **Códigos que son categorías:** `Region_Code` y `Policy_Sales_Channel` vienen como decimales, pero no tienen orden numérico.
- **Categorías raras:** 92 de los 155 canales tienen menos de 100 filas. 2 canales del `test.csv` no aparecen en `train.csv`; las regiones sí coinciden.
- **Edad:** la aceptación no crece de forma lineal: 3,5 % (20-25), 11,3 % (26-35), 21,5 % (36-45), 19,7 % (46-55), 14,1 % (56-65), 8,3 % (66 o más).
- **Variables relacionadas:** `Previously_Insured` y `Vehicle_Damage` casi se oponen: el 91 % de los clientes está en "ya asegurado y sin daño" o en "no asegurado y con daño".
- **Train y test se parecen:** edad media 38,8 en ambos; prima media 30.564 contra 30.525; `Vintage` medio 154,3 en ambos.
- **Datos personales:** no hay nombres ni documentos. `Gender` y `Age` son sensibles para la equidad.

## Sospechas de fuga de información

- No hay una columna evidente que se conozca después de la decisión.
- `Previously_Insured` tiene correlación de -0,34 con el objetivo y `Vehicle_Damage` de 0,35. Son señales fuertes pero plausibles (quien ya tiene seguro no compra otro).
- `Vintage` no muestra relación con el objetivo (correlación -0,001); se medirá con y sin ella en la etapa 4.

## Decisiones

> Mínimo **5**. Cada una con una cifra que la respalda, una acción concreta y un motivo.

| # | Hallazgo (con cifra) | Decisión | Motivo |
|---|---|---|---|
| 1 | `Response` es 12,26 % de 1 | Partir con estratificación por `Response` y evaluar con PR-AUC | La exactitud engaña con este desbalance |
| 2 | `Previously_Insured`: 22,5 % vs 0,1 % de aceptación | Conservarla y confirmar que no es fuga | Es la señal más fuerte y plausible |
| 3 | `Vehicle_Damage` y `Vehicle_Age` vienen como texto | Convertir `Vehicle_Damage` a 0/1 y `Vehicle_Age` a orden 0-1-2, dentro del `Pipeline` | Los modelos necesitan números y la antigüedad tiene orden |
| 4 | `Annual_Premium`: 17 % vale 2.630; máx. 540.165 vs p99 72.963 | Añadir indicador del valor 2.630 y tratar extremos (recorte o logaritmo) | Parece un mínimo impuesto y los extremos distorsionan modelos lineales |
| 5 | `Region_Code` (53) y `Policy_Sales_Channel` (155) son categorías | Tratarlas como categóricas, agrupando canales con menos de 100 filas en "otros" | Sin orden numérico; 92 canales raros y 2 nuevos en test |
| 6 | `Age`: aceptación 3,5 % → 21,5 % → 8,3 % según el tramo | Usar la edad con modelos que capturen relaciones no lineales, o por tramos | Una relación recta no representa la curva |
| 7 | `Vintage` sin relación con el objetivo (correlación -0,001) | Dejarla y medir el modelo con y sin ella | Probablemente es ruido; se decide con evidencia en la etapa 4 |

## Qué queda abierto

- Confirmar el enlace y la licencia del dataset.
- Medir con y sin `Vintage`, y decidir qué hacer con `Driving_License` (0,2 % con valor 0).
- Revisar equidad por `Gender` y `Age` en la validación.
- Definir con el negocio el costo de cada tipo de error, para elegir el umbral de contacto.
