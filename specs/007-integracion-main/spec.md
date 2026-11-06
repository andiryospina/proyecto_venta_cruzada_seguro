# Especificación: Integrar `main` sobre el modelo final de la rama (`007-integracion-main`)

**Rama**: `006-registro-modelo` (la integración se hace aquí y luego se propone a `main` con un *pull request*)
**Fecha**: 2026-11-06 · **Estado**: borrador, pendiente de aprobación del grupo
**Entrada**: pedido de Andiry (2026-11-06): "las etapas 7 y 8 deben ser sin `Policy_Sales_Channel` y conservando `Gender`" y
"las nuevas variables deben estar incluidas"; decisión: "las 5 de mi rama" y "sí, reemplazar en `main`".

## Por qué hace falta

Hoy hay **dos modelos finales** en el repositorio:

| | Rama `006-registro-modelo` (Andiry) | `main` (grupo, PR #1) |
|---|---|---|
| Sin `Policy_Sales_Channel` / con `Gender` | sí / sí | sí / sí |
| Variables nuevas | **5 incluidas** (`uninsured_with_damage`, `damage_x_vehicle_age`, `is_young_customer`, `age_peak_distance`, `premium_per_age`) | ninguna (la etapa 4 de `main` descartó sus propias 5 ideas) |
| `Vintage`, `Driving_License` | se conservan | se retiran (D12) |
| Hiperparámetros | Optuna, ensayo #13 | de partida (D14) |
| Clientes de entrenamiento | 304.238 (sin filas repetidas) | 304.887 |
| Prueba abierta | 2026-11-05 20:43 | 2026-11-05 19:09 |
| Código de `src/` | el de la rama | reescrito: limpieza, variables, entrenamiento y optimización distintos |

El grupo decidió que **el modelo final es el de la rama** porque debe incluir las 5 variables nuevas. Fusionar `main` tal cual no
sirve: Git no marca conflicto en `src/` (la rama no tocó esos archivos), así que se quedaría con el código de `main`, que **no calcula
las 5 variables** y **no tiene 8 de las 9 funciones** que usan los notebooks 07 y 08. Además, `models/final_pipeline.joblib` no se
podría cargar, y la etapa 9 y la app fallarían.

## Escenarios de uso y pruebas *(obligatorio)*

### Historia 1: Un solo modelo final coherente en el repositorio (Prioridad: P1)

Cualquier integrante clona el repositorio después de la integración y encuentra **un solo** modelo final, sin `Policy_Sales_Channel`,
con `Gender` y con las 5 variables nuevas. El código de `src/` lo puede volver a construir, y las pruebas pasan.

**Por qué esta prioridad**: sin esto, todo lo demás (app, informe, presentación) se apoya en un modelo que no existe en el código.

**Prueba independiente**: con el repositorio integrado, cargar `models/final_pipeline.joblib`, predecir 200 clientes de entrenamiento
y ejecutar `pytest`. Se puede hacer sin tocar la app ni los informes.

**Escenarios de aceptación**:

1. **Dado** el repositorio integrado, **cuando** se carga el modelo final, **entonces** se carga sin errores y sus variables de entrada
   incluyen `Gender`, no incluyen `Policy_Sales_Channel`, y el modelo calcula las 5 variables nuevas.
2. **Dado** el repositorio integrado, **cuando** se ejecuta `pytest`, **entonces** todas las pruebas pasan.
3. **Dado** que en `main` había archivos que la rama no tenía (inferencia, registro de decisiones, informe, presentación, scripts),
   **cuando** se integra, **entonces** siguen en el repositorio (adaptados o sin cambios), y ninguno se pierde sin que se anote por qué.

---

### Historia 2: Las cifras y decisiones escritas dicen la verdad (Prioridad: P1)

Quien lea `reports/` (informe técnico, validación, registro de decisiones) ve las cifras del modelo final de la rama, sin mezclas con las
del modelo de `main`, y entiende por qué cambió la decisión del grupo.

**Por qué esta prioridad**: el informe es lo que se evalúa. Una cifra del modelo equivocado es un dato falso (principio VII).

**Prueba independiente**: comparar cada cifra de prueba que aparece en `reports/informe_tecnico.md`, `reports/07_validacion.md` y
`presentacion/ejecutiva.md` con `reports/07_metricas_test.json` de la rama.

**Escenarios de aceptación**:

1. **Dado** el registro de decisiones del grupo, **cuando** se lee D14 y la decisión de la etapa 4 sobre variables nuevas,
   **entonces** aparecen como **reemplazadas** (no borradas), con fecha, el motivo ("el grupo exige incluir las 5 variables nuevas")
   y la nueva decisión.
2. **Dado** P12 (los 649 clientes), **cuando** se lee, **entonces** queda cerrado con la explicación: son filas que quedaron
   repetidas al quitar `Policy_Sales_Channel`, y la limpieza de la rama las elimina.
3. **Dado** que la prueba se abrió dos veces en el grupo (19:09 con el modelo de `main` y 20:43 con el de la rama), **cuando** se lee
   el informe de validación y el informe técnico, **entonces** lo dicen explícitamente, junto con que la elección del modelo final se
   hizo por un criterio fijado sin mirar la prueba (incluir las variables nuevas) y no por comparar sus cifras de prueba.
4. **Dado** cualquier cifra de prueba en los informes, **cuando** se compara con `reports/07_metricas_test.json` de la rama,
   **entonces** coincide. Ninguna cifra se recalcula sobre la prueba.

---

### Historia 3: La app y la inferencia usan el modelo final (Prioridad: P2)

Una persona abre la app, llena el formulario y recibe la recomendación (llamar o no) que da el modelo final de la rama, con validación
de entradas y aviso de uso responsable.

**Por qué esta prioridad**: es lo que ve el usuario de negocio, pero depende de que la historia 1 esté resuelta.

**Prueba independiente**: ejecutar las pruebas de inferencia y abrir la app con un cliente de ejemplo.

**Escenarios de aceptación**:

1. **Dado** `models/model.joblib`, **cuando** se carga, **entonces** es el mismo modelo que `models/final_pipeline.joblib` (mismas
   probabilidades en 200 clientes, diferencia máxima ≤ 1e-9).
2. **Dado** el formulario de la app, **cuando** se llena, **entonces** pide los datos que necesita el modelo de la rama, incluidos
   `Vintage` y `Driving_License`, y no pide `Policy_Sales_Channel`.
3. **Dado** un valor fuera de rango (por ejemplo, edad 150 o prima negativa), **cuando** se envía, **entonces** la app lo rechaza con
   un mensaje claro y no predice.
4. **Dado** cualquier predicción, **cuando** se muestra, **entonces** usa el umbral 1/6 y aparece el aviso de uso responsable.
5. **Dado** el código de la app, **cuando** se revisa, **entonces** no consulta Databricks.

---

### Historia 4: Nada personal en el repositorio público (Prioridad: P2)

**Por qué esta prioridad**: el repositorio es público (principio V).

**Prueba independiente**: buscar direcciones de correo en los archivos versionados (sin contar `material-del-curso/`).

**Escenarios de aceptación**:

1. **Dado** el repositorio integrado, **cuando** se buscan correos personales, **entonces** no aparece ninguno. Hoy aparecen en
   `reports/08_registro.json`, `reports/08_registro.md` y `notebooks/08_registro_modelo.ipynb` de `main`.

### Casos límite

- **Un archivo de `main` depende del código de `main` que se va** (por ejemplo, `src/proyecto/inference/serving.py` o
  `tests/test_tournament.py`): se adapta al código de la rama; si no tiene sentido sin el código de `main`, se quita y se anota por qué
  en `reports/`.
- **Pruebas de `main` sobre funciones que ya no existen**: no se dejan fallando ni se borran en silencio. Se quitan junto con su
  función y se anota en el reporte de integración qué se quitó y por qué.
- **El modelo de `main` registrado en Databricks** (`workspace.default.venta_cruzada_seguros`, v1, alias `champion`): no se borra.
  Al registrar el modelo de la rama, el alias `champion` debe pasar a la versión nueva.
- **`models/model.joblib` de `main` pesa y tiene el modelo viejo**: se reemplaza por el de la rama; no quedan dos modelos con el mismo
  nombre.
- **Notebooks 03 a 06 de `main`**: muestran resultados del código de `main`. Se conserva la versión de la rama de los notebooks 03 a 06
  para que coincidan con el código oficial; los informes 04 a 06 de `main` que cambian cifras se revisan contra la rama.
- **Sin conexión con Databricks**: la integración y la app no la necesitan. Solo el registro del modelo (tarea pendiente T009 de
  `006-registro-modelo`) la usa.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **FR-001**: El código oficial de `src/proyecto/` (limpieza, partición, variables, entrenamiento, optimización, validación, registro)
  y sus pruebas en `tests/` MUST ser el de la rama `006-registro-modelo`.
- **FR-002**: En los 8 archivos con conflicto (`especificacion-proyecto.md`, `notebooks/07_validacion_interpretacion.ipynb`,
  `notebooks/08_registro_modelo.ipynb`, `reports/06_best_params.json`, `reports/07_decisiones_congeladas.json`,
  `reports/07_metricas_test.json`, `reports/07_validacion.md`, `reports/prueba_abierta.txt`) MUST quedar la versión de la rama.
  Excepciones: `especificacion-proyecto.md` y `reports/prueba_abierta.txt` MUST conservar también lo que agregó `main` que siga siendo
  cierto (por ejemplo, la primera apertura de la prueba a las 19:09).
- **FR-003**: De `main` MUST conservarse lo que no choca con el modelo de la rama: `src/proyecto/inference/` (adaptado), el registro de
  decisiones del grupo, el informe técnico, la presentación, los scripts, la app (adaptada) y las especificaciones que agregó.
- **FR-004**: Cada archivo de `main` que se quite o se reemplace MUST quedar listado, con su motivo, en un reporte de integración en
  `reports/`.
- **FR-005**: El registro de decisiones del grupo MUST marcar D14 y la decisión de la etapa 4 sobre variables nuevas como
  **reemplazadas** (con fecha, motivo y nueva decisión), cerrar P12 con su explicación y revisar D12 (en el modelo final siguen
  `Vintage` y `Driving_License`).
- **FR-006**: El informe de validación y el informe técnico MUST declarar que la prueba se abrió dos veces en el grupo y que el modelo
  final se eligió por un criterio fijado antes de comparar cifras de prueba.
- **FR-007**: Ninguna métrica MUST recalcularse sobre la prueba. Toda cifra de prueba en informes, presentación y app MUST salir de
  `reports/07_metricas_test.json` de la rama.
- **FR-008**: La etapa 9 (inferencia), `models/model.joblib`, `models/input_schema.json` y la app MUST rehacerse sobre el modelo de la
  rama: mismas probabilidades que `models/final_pipeline.joblib`, umbral 1/6, validación de entradas y aviso de uso responsable, sin
  consultar Databricks.
- **FR-009**: El informe técnico, `models/ficha_modelo.md`, `reports/09_despliegue.md` y `presentacion/ejecutiva.md` MUST describir el
  modelo de la rama (variables, parámetros, cifras).
- **FR-010**: Ningún archivo versionado MUST contener correos personales, tokens ni la dirección del workspace de Databricks.
- **FR-011**: Al terminar, `pytest` MUST pasar completo, y cada función de `src/` que limpia o transforma datos MUST tener su prueba.
- **FR-012**: El resultado MUST proponerse a `main` con un *pull request* que el grupo revisa; no se escribe directo en `main`.

### Entidades clave

- **Modelo final**: el `Pipeline` de la rama (variables nuevas + preprocesamiento + LightGBM con parámetros del ensayo #13), guardado
  en `models/final_pipeline.joblib` y copiado como `models/model.joblib` para la app.
- **Cifras de la prueba**: `reports/07_metricas_test.json` de la rama; única fuente de cifras de prueba.
- **Registro de decisiones del grupo**: `reports/decisiones_del_grupo.md` (viene de `main`), con estados DECIDIDO, ADOPTADO,
  REEMPLAZADO y PENDIENTE.
- **Reporte de integración**: lista de lo que se tomó de cada lado, lo que se quitó y por qué.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: El 100 % de las pruebas pasa al final de la integración.
- **SC-002**: Hay **1** modelo final en el repositorio: `models/model.joblib` y `models/final_pipeline.joblib` dan las mismas
  probabilidades en 200 clientes (diferencia máxima ≤ 1e-9).
- **SC-003**: El 100 % de las cifras de prueba citadas en el informe técnico, el informe de validación, la ficha del modelo y la
  presentación coinciden con `reports/07_metricas_test.json` de la rama (0 cifras del modelo de `main` como resultado vigente).
- **SC-004**: **0** correos personales, tokens o direcciones del workspace en los archivos versionados.
- **SC-005**: **0** archivos de `main` quitados sin aparecer en el reporte de integración.
- **SC-006**: Una persona del grupo abre la app, llena el formulario de un cliente y obtiene la recomendación en menos de 1 minuto.

## Supuestos

- **Las 649 filas (P12)** son clientes que quedaron repetidos al quitar `Policy_Sales_Channel`. La limpieza de la rama los quita, así
  que el modelo final se entrenó con 304.238 clientes. La prueba (76.222 clientes) es idéntica en las dos versiones.
- **Registro en Databricks**: el modelo de la rama se registra como una **versión nueva del nombre que ya usa el grupo**
  (`workspace.default.venta_cruzada_seguros`) y recibe el alias `champion`; la v1 de `main` queda como historia. Lo hace la tarea
  pendiente T009 de `006-registro-modelo`, dentro de Databricks; esta integración no reentrena ni registra.
- **Regresión logística como alternativa explicable (D10)**: se conserva en el registro de decisiones como está; no se reentrena.
- **Auditoría de equidad por `Gender` y edad (D12)**: la hace la etapa 07 de la rama (`reports/07_segmentos.csv`); se cita, no se rehace.
- **Notebooks 01 y 02 de `main`** (caso de negocio y EDA): se conservan de `main` si no chocan con el código de la rama.
- La integración se hace en la rama `006-registro-modelo` (o en una rama nueva salida de ella, decisión del plan) y llega a `main` por
  *pull request*.

## Fuera de alcance

- Reentrenar, volver a optimizar o volver a evaluar el modelo sobre la prueba.
- Medir de nuevo con y sin `Vintage`, `Driving_License` o las variables nuevas.
- Borrar la versión 1 del modelo de `main` en Databricks.
