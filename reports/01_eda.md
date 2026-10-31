# Informe del EDA

> Resultado de `notebooks/02_eda.ipynb` (ejecutado el 2026-10-31 con el entorno `.venv`). Cada hallazgo termina en una decisión;
> las decisiones se implementan con pruebas en `src/proyecto/data/` en la etapa 03.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`.

## Qué son los datos

- **Filas × columnas:** 381.109 × 12 (`dataset.csv`, *Health Insurance Cross Sell Prediction*).
- **Unidad de análisis (qué es una fila):** un cliente actual del seguro de salud, con los datos de su vehículo y su respuesta a la oferta
  de seguro de vehículo.
- **¿Una entidad aparece en varias filas?** No: los 381.109 `id` son distintos. La partición se hace por fila, estratificada por `Response`.
- **Objetivo y distribución:** `Response` (1 = interesado). 46.710 interesados (**12,26 %**) y 334.399 no interesados (87,74 %). Sin vacíos.
- **Línea base** (resultado de una regla trivial): predecir siempre "no interesado" acierta el 87,74 % y no encuentra a nadie, así que la
  exactitud no sirve. En costo esperado por cliente (matriz 5 a 1), la mejor regla simple da 0,373 (ver `reports/00_caso.md`).

## Calidad de los datos

- Sin valores vacíos en ninguna columna y sin filas duplicadas exactas.
- **269 filas repetidas** si se ignora el `id` (0,07 %); en 53 de esos grupos la misma combinación de variables tiene respuestas distintas.
- **`Annual_Premium` tiene un piso:** el valor 2.630 aparece en **64.877 filas (17,02 %)** y el siguiente valor es 6.098. Su tasa de
  interés (13,1 %) es parecida a la del resto (12,1 %).
- **`Annual_Premium` tiene cola larga:** mediana 31.669, p99 72.963, máximo 540.165; 10.320 filas (2,71 %) superan el límite IQR (61.892).
- **`Region_Code` (53 códigos) y `Policy_Sales_Channel` (155 códigos) son etiquetas guardadas como decimal.** 134 canales tienen menos de
  1.000 filas (4,12 % del total); los 5 canales mayores cubren el 84,2 %.
- **`Driving_License = 0` solo en 812 filas (0,21 %):** casi constante.
- `Age` (20–85) y `Vintage` (10–299 días) no tienen valores imposibles. No hay variables que deban ser estables entre filas (cada cliente aparece una vez).
- **Datos personales:** no hay nombres, documentos ni teléfonos. `Gender` y `Age` son atributos sensibles (ver decisión 10).

## Relación de cada variable con la respuesta

Medida solo en la porción de exploración (80 %, estratificada, semilla 42: 304.887 clientes, tasa 12,26 %). El 20 % de prueba no se miró.

| Fuerza | Variable | Evidencia |
|---|---|---|
| **Fuerte** | `Vehicle_Damage` | Con daño previo 23,8 % se interesa; sin daño 0,5 %. V de Cramér 0,354; información mutua 0,080 |
| **Fuerte** | `Previously_Insured` | Sin seguro de vehículo 22,6 %; ya asegurado 0,08 %. V 0,341; IM 0,079 |
| **Media** | `Policy_Sales_Channel` | Entre canales con ≥ 1.000 clientes, la tasa va de 2,2 % a 32,7 %; los canales 152 y 160 (41 % de la base) convierten menos del 3 %. V 0,263 |
| **Media** | `Vehicle_Age` | < 1 año 4,4 %; 1–2 años 17,4 %; > 2 años 29,3 %. V 0,221 |
| **Media** | `Age` | Forma de campana: 3,6 % entre 20 y 25 años, cerca de 22 % entre 35 y 50, 6,6 % desde los 80. Pearson 0,111, Spearman 0,144, AUC 0,627; mediana 34 (no) vs 43 (sí) |
| Débil | `Region_Code` | Entre regiones con ≥ 1.000 clientes la tasa va de 4,6 % a 18,8 %. V 0,137 |
| Muy débil | `Gender` | Hombres 13,8 %, mujeres 10,4 %. V 0,051 |
| Muy débil | `Annual_Premium` | Pearson 0,022, AUC 0,530; mediana 31.526 (no) vs 33.057 (sí) |
| Ninguna | `Vintage` | Pearson −0,002 (p = 0,38), AUC 0,499; distribuciones iguales en los dos grupos |
| Ninguna | `Driving_License` | V 0,010; IM 0,0001 |

**Matriz de correlación:** las variables más relacionadas con `Response` son `Vehicle_Damage` (+0,35), `Previously_Insured` (−0,34),
`Vehicle_Age` (+0,22) y `Age` (+0,11 Pearson / +0,14 Spearman). Hay dos pares redundantes: `Previously_Insured`–`Vehicle_Damage`
(−0,82) y `Age`–`Vehicle_Age` (+0,82 Spearman, +0,77 Pearson).

**Interacción:** quien ya tiene seguro de vehículo casi nunca se interesa (≤ 3,6 % en todas las combinaciones); quien no lo tiene y tuvo
daño llega a 15,4 %–29,4 % según la antigüedad del vehículo.

**Implicación:** la señal se concentra en 2–3 variables y varias relaciones no son lineales (edad, canal, región); conviene comparar
regresión logística con modelos de árboles en el torneo.

## Datos atípicos y decisiones de negocio (2026-10-31)

Revisión en la porción de exploración (304.887 filas) con percentiles, IQR × 1,5, IQR × 3 y |z| > 3.

| Variable | Rango p1 – p99 | Máximo | Fuera de IQR × 1,5 | Lectura | Decisión (con input de negocio) |
|---|---|---|---|---|---|
| `Age` | 20 – 77 | 85 | 0 | Rango adulto normal | Ninguna |
| `Vintage` | 12 – 297 | 299 | 0 | Rango acotado | Ninguna |
| `Annual_Premium` (cola alta) | 2.630 – 73.132 | 540.165 | 8.280 (2,72 %) | 250 valores distintos sobre el p99,9; la tasa de interés **sube** con la prima (15,0 % → 16,9 %): son clientes reales | **No borrar.** Recortar al p99,9 de entrenamiento (tope aprendido: **115.478**, afecta a 305 clientes, 0,10 %) y aplicar `log1p`, dentro del `Pipeline` |
| `Annual_Premium` = 2.630 | — | — | — | 17,02 % de clientes; siguiente valor 6.098 | Negocio: **es la prima mínima del producto**. Conservar y marcar con `is_min_premium` |
| `Driving_License` = 0 | — | — | — | 654 clientes (0,21 %), mediana 67 años | Negocio: **se conservan** (pueden asegurar un vehículo que conduce otra persona) |

Resultado del preprocesamiento (`notebooks/03_preprocesamiento.ipynb`): 304.238 filas de entrenamiento (649 repetidas quitadas) y
76.222 de prueba, ambas con 12,26 % de interesados; `Policy_Sales_Channel` eliminada (decisión 8); región 53 → 48 categorías +
"otros"; 58 columnas listas para modelar. Sin el canal hay más perfiles idénticos (649 en vez de 177, 0,21 % del entrenamiento).

## Sospechas de fuga de información

- Ninguna columna es casi idéntica al objetivo: la pureza media por categoría (0,83–0,91) es la misma que da la clase mayoritaria (0,88).
- **`Policy_Sales_Channel`:** es el canal por el que se contactó al cliente. Si se asigna en la campaña, no se conoce antes de decidir a
  quién llamar. **Decisión (2026-10-31): se elimina del modelo** (decisión 8).

## Decisiones

| # | Hallazgo (con cifra) | Decisión | Motivo |
|---|---|---|---|
| 1 | `id` único en las 381.109 filas; `Response` 12,26 % positivos | Partir por fila, estratificado por `Response`: 80 % entrenamiento/validación y 20 % prueba, `random_state=42`; validación cruzada `StratifiedKFold` | No hay clientes repetidos; la estratificación conserva la proporción de interesados |
| 2 | `id` es un consecutivo sin significado | Quitar `id` de las variables al cargar | No describe al cliente; el modelo podría memorizarlo |
| 3 | 269 filas repetidas sin contar `id` (0,07 %); 53 grupos con respuesta contradictoria | Quitar repetidas solo en entrenamiento, conservando la primera | Evita contar dos veces el mismo perfil; no se toca la prueba |
| 4 | `Annual_Premium` = 2.630 en 17,02 % de las filas (siguiente valor 6.098) | Crear `is_min_premium` y conservar el valor | Es un piso o valor por defecto, no un monto comparable |
| 5 | `Annual_Premium` con cola larga (máx. 540.165; 2,71 % sobre el límite IQR) | Aplicar `log1p` dentro del `Pipeline` | Reduce el peso de los extremos sin borrar filas |
| 6 | `Region_Code` y `Policy_Sales_Channel` son códigos en decimal; 134 canales con < 1.000 filas (4,12 %) | Convertir a categoría entera y agrupar en `"otros"` las categorías con < 1.000 filas de entrenamiento (dentro del `Pipeline`) | Son etiquetas, no cantidades; las categorías raras dan tasas inestables |
| 7 | `Vehicle_Age` ordenada (4,4 % → 17,4 % → 29,3 %); `Vehicle_Damage` y `Gender` binarias en texto | Codificar `Vehicle_Age` como 0/1/2 y las binarias como 0/1 | Conserva el orden real y deja las columnas listas para cualquier modelo |
| 8 | `Policy_Sales_Channel` es el canal de contacto; V de Cramér 0,263 | **Eliminarla** al limpiar (decisión del grupo, 2026-10-31; antes: medir con y sin ella) | Si se decide en la campaña, no estaría disponible antes de llamar: es una posible fuga. Se pierde señal (V 0,263) a cambio de un modelo usable al decidir |
| 9 | `Vintage` (AUC 0,499) y `Driving_License` (0,21 % en 0; V 0,010) sin relación con `Response` | Conservarlas en el preprocesamiento; candidatas a salir en la etapa 04 | Se quitan solo si la validación confirma que no aportan |
| 10 | Hombres 13,8 % vs mujeres 10,4 %; tasa por edad de 3,6 % a 22 % | Evaluar el modelo con y sin `Gender` y reportar recall por género y tramo de edad | Atributos sensibles: el modelo no debe dejar de contactar a un grupo sin razón de negocio |

## Qué queda abierto

- `Policy_Sales_Channel` se eliminó (decisión 8). Si el negocio confirma que el canal se conoce antes de llamar, se puede reincorporar y medir.
- Confirmar qué significa la prima 2.630 (¿prima mínima del producto o valor por defecto?).
- Validar la relación de costos 5 a 1 de `reports/00_caso.md`.
- Mover `dataset.csv` a `data/raw/` y decidir si se retira del historial de Git (la licencia sigue por confirmar).
