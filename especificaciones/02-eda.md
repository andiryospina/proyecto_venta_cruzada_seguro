# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.

**Grupo:** _______________   **Fecha:** 2026-10-31   **Estado:** ☒ borrador  ☐ cerrada

> Nota: esta especificación la redactó Claude a partir de la ficha del caso y de la ejecución del notebook. Las hipótesis de la sección 1
> no se escribieron "a ciegas": el grupo debe revisarlas y marcar la especificación como cerrada.

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

| Pregunta | Lo que creemos |
|---|---|
| ¿Qué representa una fila? | Un cliente actual del seguro de salud y su respuesta a la oferta de seguro de vehículo. **Se cumplió.** |
| ¿Alguna entidad se repite en varias filas? | No: `id` debería ser único. **Se cumplió** (381.109 `id` distintos). |
| ¿Qué variable **debería** ser estable y no cambiar? | No aplica: cada cliente aparece una sola vez. |
| ¿Qué significaría un vacío en nuestras columnas clave? | Dato no registrado; no esperamos vacíos en un dataset de competencia. **Se cumplió** (0 vacíos). |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | `Response` (objetivo). Sospecha: `Policy_Sales_Channel`, si el canal se asigna en la campaña. |

## 2. Qué vamos a medir

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☐ sí ☒ no: todas las numéricas llegan como número; los códigos llegan como decimal (ver 3.8) | `Region_Code`, `Policy_Sales_Channel` | |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☒ sí ☐ no: | `Annual_Premium` (valor 2.630 repetido en 17 %) | |
| 3.3 Valores imposibles (percentiles, negativos) | ☒ sí ☐ no: | `Age`, `Annual_Premium`, `Vintage` | |
| 3.4 Constancia por entidad | ☐ sí ☒ no: cada cliente aparece una vez | — | |
| 3.5 Vacíos que significan algo | ☐ sí ☒ no: no hay vacíos | — | |
| 3.6 Duplicados | ☒ sí ☐ no: | todas menos `id` | |
| 3.7 Fechas y orden temporal | ☐ sí ☒ no: no hay columnas de fecha; `Vintage` son días como cliente | — | |
| 3.8 Categorías raras / alta cardinalidad | ☒ sí ☐ no: | `Region_Code` (53), `Policy_Sales_Channel` (155) | |
| 3.9 Identidad y datos personales | ☒ sí ☐ no: | `id`, `Gender`, `Age` | |
| Relación de cada variable con `Response` (pedido del grupo) | ☒ sí ☐ no: | todas, solo en el 80 % de exploración | |

## 3. Lo que medimos (se llena mientras corre el notebook)

- **Filas × columnas:** 381.109 × 12
- **Unidad de análisis (una frase):** un cliente del seguro de salud con su vehículo y su respuesta a la oferta de seguro de vehículo.
- **Columna que identifica a la entidad (`ID_COL`):** `id`   **¿Se repite?** ☒ no ☐ sí
- **Objetivo (`TARGET`):** `Response`   **Distribución:** 12,26 % interesados (46.710), 87,74 % no interesados (334.399)
- **Línea base** (regla trivial) y su resultado: siempre "no interesado" = 87,74 % de exactitud y 0 interesados encontrados; regla
  "sin seguro previo y con daño" = costo esperado 0,373 por cliente (matriz 5 a 1).
- **Vacíos en el objetivo:** 0   **Qué haremos con esas filas:** no aplica
- **Datos personales encontrados:** ningún identificador directo; `Gender` y `Age` son atributos sensibles; `id` se elimina de las variables.
- **Columnas sospechosas de fuga:** `Policy_Sales_Channel` (eliminada en la limpieza, decisión 8)

## 4. Decisiones (mínimo 5)

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | `id` único en 381.109 filas; 12,26 % positivos | Partición por fila estratificada por `Response`, 80/20, `random_state=42`; `StratifiedKFold` | No hay clientes repetidos; conserva la proporción de interesados | `split_train_test` |
| 2 | `id` es un consecutivo sin significado | Quitar `id` al cargar | No describe al cliente | `drop_id_column` |
| 3 | 269 filas repetidas sin `id` (0,07 %) | Quitarlas solo en entrenamiento | Evita contar dos veces un perfil | `drop_duplicate_rows` |
| 4 | `Annual_Premium` = 2.630 en 17,02 % (siguiente valor 6.098) | Crear `is_min_premium` y conservar el valor | Es un piso o valor por defecto | `add_min_premium_flag` |
| 5 | `Annual_Premium` máx. 540.165; 2,71 % sobre el límite IQR | `log1p` dentro del `Pipeline` | Reduce el peso de los extremos sin borrar filas | `log_transform_premium` |
| 6 | Códigos en decimal; 134 canales con < 1.000 filas (4,12 %) | Categoría entera + agrupar raras en `"otros"` (aprendido en entrenamiento) | Son etiquetas; categorías raras dan tasas inestables | `cast_codes_to_category`, `group_rare_categories` |
| 7 | `Vehicle_Age` ordenada; `Vehicle_Damage` y `Gender` en texto | `Vehicle_Age` 0/1/2; binarias 0/1 | Conserva el orden real | `encode_categoricals` |
| 8 | `Policy_Sales_Channel` posible fuga (V 0,263) | **Eliminarla** al limpiar (decisión del grupo, 2026-10-31) | Puede no conocerse antes de llamar | `drop_excluded_columns` |
| 9 | `Vintage` (AUC 0,499) y `Driving_License` (V 0,010) sin relación | Conservar; candidatas a salir en etapa 4 | Se quitan solo si la validación lo confirma | — (etapa 4) |
| 10 | Hombres 13,8 % vs mujeres 10,4 % | Evaluar con y sin `Gender`; recall por grupo | Equidad | — (etapas 4 y 7) |

## 5. Criterios de cierre

- ☒ `notebooks/02_eda.ipynb` corre de principio a fin sin errores.
- ☒ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☒ Al menos **5 decisiones** con cifra, acción y motivo.
- ☒ Datos personales identificados y plan para eliminarlos al cargar.
- ☒ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☒ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☒ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
