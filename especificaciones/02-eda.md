# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.

**Grupo:** _______________   **Fecha:** _______________   **Estado:** ☐ borrador  ☐ cerrada

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

Una hipótesis por pregunta. Si después no se cumple, es un hallazgo: anótenlo.

| Pregunta | Lo que creemos |
|---|---|
| ¿Qué representa una fila? | |
| ¿Alguna entidad se repite en varias filas? | |
| ¿Qué variable **debería** ser estable y no cambiar? | |
| ¿Qué significaría un vacío en nuestras columnas clave? | |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | |

## 2. Qué vamos a medir

> **BORRADOR.** Las secciones 2 a 4 se prellenaron con una primera medición sobre `data/raw/train.csv`.
> La sección 1 (hipótesis previas) queda para el grupo: ya se miraron los datos, así que no se puede escribir "antes de mirar".
> El grupo debe verificar estas cifras en `notebooks/02_eda.ipynb` y decidir quién hace cada chequeo.

Marquen lo que aplica a su dataset. Lo que no aplique se tacha **con una razón** (no se deja en blanco).

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☐ sí ☒ no: las columnas de texto son `Gender`, `Vehicle_Age`, `Vehicle_Damage` y son categorías reales | | |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☒ sí ☐ no: | `Annual_Premium` (17 % vale 2.630) | |
| 3.3 Valores imposibles (percentiles, negativos) | ☒ sí ☐ no: | `Annual_Premium` (máx. 540.165; p99 72.963) | |
| 3.4 Constancia por entidad | ☐ sí ☒ no: cada `id` aparece una sola vez | | |
| 3.5 Vacíos que significan algo | ☐ sí ☒ no: 0 nulos en `train.csv` | | |
| 3.6 Duplicados | ☒ sí ☐ no: | filas completas (0 encontradas) | |
| 3.7 Fechas y orden temporal | ☐ sí ☒ no: no hay columnas de fecha | | |
| 3.8 Categorías raras / alta cardinalidad | ☒ sí ☐ no: | `Region_Code` (53), `Policy_Sales_Channel` (155), `Driving_License` (812 filas con 0) | |
| 3.9 Identidad y datos personales | ☒ sí ☐ no: no hay datos de identidad; revisar `Gender` y `Age` por equidad | | |

## 3. Lo que medimos (se llena mientras corre el notebook)

- **Filas × columnas:** 381.109 × 12 (`train.csv`)
- **Unidad de análisis (una frase):** un cliente con seguro de salud y la respuesta a la oferta de seguro de vehículo. **[El grupo confirma]**
- **Columna que identifica a la entidad (`ID_COL`):** `id`   **¿Se repite?** ☒ no ☐ sí
- **Objetivo (`TARGET`):** `Response`   **Distribución:** 0 = 87,74 %, 1 = 12,26 %
- **Línea base** (regla trivial) y su resultado: "siempre 0" acierta el 87,7 % y no encuentra a ningún comprador; PR-AUC pendiente de medir.
- **Vacíos en el objetivo:** 0   **Qué haremos con esas filas:** nada
- **Datos personales encontrados:** ninguno directo; `Gender` y `Age` son sensibles.
- **Columnas sospechosas de fuga:** ninguna evidente; revisar `Vintage` (se miden con y sin ella en la etapa 4)

## 4. Decisiones (mínimo 5)

> Cada una con **cifra**, acción **concreta** y **motivo**. Se copian tal cual a `reports/01_eda.md`.
> Cada decisión se convierte en una función de `src/proyecto/data/` y en una prueba (ver `03-preprocesamiento.md`).
> Estas cinco son **propuestas** a partir de la primera medición; el grupo las aprueba o las cambia.

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | `Response` es 12,26 % de 1 | Partir con estratificación por `Response` y evaluar con PR-AUC | La exactitud engaña con este desbalance | _(por definir en `src/proyecto/data/`)_ |
| 2 | `Previously_Insured`: acepta 22,5 % de quienes no tenían seguro y 0,1 % de quienes sí | Conservarla y confirmar que no es fuga | Es la señal más fuerte; si es demasiado perfecta hay que revisarla | _(por definir)_ |
| 3 | `Vehicle_Damage`: acepta 23,8 % con daño previo y 0,5 % sin él | Convertir Yes/No a 0/1 dentro del `Pipeline` | Variable binaria en texto | _(por definir)_ |
| 4 | `Annual_Premium`: 17 % vale 2.630; máx. 540.165 vs p99 72.963 | Marcar el valor 2.630 con una columna indicadora y tratar los extremos (recorte o logaritmo) | Parece un mínimo impuesto y los extremos distorsionan los modelos lineales | _(por definir)_ |
| 5 | `Region_Code` (53 valores) y `Policy_Sales_Channel` (155) son números pero son categorías | Tratarlas como categóricas, agrupando las raras | Sus valores no tienen orden numérico | _(por definir)_ |

## 5. Criterios de cierre

- ☐ `notebooks/02_eda.ipynb` corre de principio a fin sin errores.
- ☐ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☐ Al menos **5 decisiones** con cifra, acción y motivo.
- ☐ Datos personales identificados y plan para eliminarlos al cargar.
- ☐ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☐ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☐ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
