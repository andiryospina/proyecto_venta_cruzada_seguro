# Especificación: App de Streamlit con pestañas que cuenta las 9 etapas (`008-app-streamlit`)

**Rama**: `008-app-streamlit` (desde el `main` local) · **Fecha**: 2026-11-06 · **Estado**: borrador; las ambigüedades se decidieron
sin consultar al grupo y quedan como **Supuestos** (el grupo puede cambiarlas)
**Entrada**: pedido de entregar una sola app que integre las etapas 1 a 9; la app actual (`app/streamlit_app.py`, 144 líneas) es solo un
formulario y **ya está desplegada** en Streamlit Community Cloud desde este repositorio (entrypoint `app/streamlit_app.py`, Python 3.12,
instala `requirements.txt` de la raíz).

## Por qué hace falta

El proyecto tiene las etapas 1 a 9 completas, pero quien abre el enlace público solo ve un formulario. No ve el caso de negocio, de dónde
salen los datos, cómo se eligió el modelo, qué tan bien funcionó en la prueba ni qué quedó pendiente. Hoy hay que leer
`reports/*.md` en GitHub para entenderlo. Se quiere **una sola app** (mismo enlace, mismo entrypoint) que cuente el proyecto de principio a
fin en pestañas y conserve el formulario de predicción.

## Escenarios de uso y pruebas *(obligatorio)*

### Historia 1: Leer el proyecto completo en un solo lugar (Prioridad: P1)

Una persona (docente, evaluadora, compañera de otro grupo) abre la app y recorre las pestañas en el orden de las etapas.

**Por qué P1**: es el motivo de la tarea; sin esto no hay entrega.

**Prueba independiente**: arrancar la app y abrir cada pestaña; todas muestran el contenido de su informe sin excepciones.

**Escenarios de aceptación**:

1. **Dado** que la app arranca, **cuando** se abre, **entonces** se ven 8 pestañas en este orden: Caso de negocio · Datos y EDA · Variables ·
   Modelos · Resultado en la prueba · Registro y ficha · Decisiones y pendientes · Probar el modelo.
2. **Dado** que existe `reports/01_eda.md`, **cuando** se abre "Datos y EDA", **entonces** se ve su texto y sus tablas (markdown de GitHub) bien dibujadas.
3. **Dado** que falta un archivo de una pestaña, **cuando** se abre esa pestaña, **entonces** aparece un aviso que nombra el archivo y el resto de la app sigue funcionando.

### Historia 2: Ver el resultado en la prueba con cifras exactas (Prioridad: P1)

**Prueba independiente**: la pestaña "Resultado en la prueba" muestra tarjetas, calibración, SHAP y segmentos.

**Escenarios de aceptación**:

1. **Dado** `reports/07_metricas_test.json`, **cuando** se abre la pestaña, **entonces** hay tarjetas con costo por cliente (con su IC 95 %), diferencia
   frente a la línea base (con su IC 95 %), % a llamar, recall, precisión, PR-AUC, ROC-AUC y captura al 20 %; cada número coincide con el JSON.
2. **Dado** que existen `07_calibracion.png` y `07_shap.png`, **cuando** se abre, **entonces** se ven ambas imágenes con su título.
3. **Dado** `07_segmentos.csv`, **cuando** se abre, **entonces** se ve la tabla por género, edad y región con porcentajes legibles.
4. **Dado** que la prueba se abrió dos veces, **cuando** se abre la pestaña, **entonces** la sección 3.1 de `07_validacion.md` se ve destacada,
   tal como está escrita en el archivo.

### Historia 3: Las advertencias honestas se ven siempre (Prioridad: P1)

**Por qué P1**: principio VII y el compromiso del grupo de decir lo que no se pudo medir.

**Escenarios de aceptación**:

1. **Dado** cualquier pestaña abierta, **cuando** se mira la parte superior de la página, **entonces** hay un bloque "Avisos importantes" con: la prueba se
   abrió dos veces; el modelo usa edad y género (con las cifras de cobertura por edad); hay N decisiones pendientes de terceros. El texto sale de
   `models/ficha_modelo.md`, `reports/prueba_abierta.txt` y `reports/decisiones_del_grupo.md`, no está reescrito.

### Historia 4: Seguir probando el modelo con el formulario (Prioridad: P1)

**Escenarios de aceptación**:

1. **Dado** la pestaña "Probar el modelo", **cuando** se pulsa **Evaluar** con los valores por defecto, **entonces** aparece "Resultado sugerido" con `LLAMAR` o
   `NO LLAMAR`, igual que antes (mismos campos, validación y casilla "No sé").
2. **Dado** que `tests/test_app.py` ya existía, **cuando** se corre, **entonces** sus 3 pruebas pasan sin cambios.

### Historia 5: Decisiones y pendientes de terceros destacados (Prioridad: P2)

**Escenarios de aceptación**:

1. **Dado** `reports/decisiones_del_grupo.md`, **cuando** se abre "Decisiones y pendientes", **entonces** la sección B (pendientes de dato externo) aparece primero y
   destacada, con una ficha desplegable por pendiente (P01 a P12), y las cerradas se marcan como cerradas.
2. **Dado** la sección A, **cuando** se abre, **entonces** la tabla de decisiones (D01 a D15) está disponible en un desplegable.

## Pestañas y fuentes

| # | Pestaña | Fuentes (solo lectura) |
|---|---|---|
| 1 | Caso de negocio | `reports/00_caso.md` |
| 2 | Datos y EDA | `reports/01_eda.md` |
| 3 | Variables | `reports/04_features.md`, `reports/04_features_tabla.csv` |
| 4 | Modelos (subpestañas Torneo · Optimización) | `reports/05_torneo.md`, `reports/06_optimizacion.md` |
| 5 | Resultado en la prueba | `reports/07_metricas_test.json`, `reports/07_validacion.md`, `reports/07_calibracion.png`, `reports/07_shap.png`, `reports/07_segmentos.csv` |
| 6 | Registro y ficha del modelo (subpestañas) | `reports/08_registro.md`, `models/ficha_modelo.md` |
| 7 | Decisiones y pendientes | `reports/decisiones_del_grupo.md` |
| 8 | Probar el modelo | `models/model.joblib`, `models/input_schema.json` (como hoy) |
| — | Avisos importantes (encima de las pestañas) | `models/ficha_modelo.md`, `reports/prueba_abierta.txt`, `reports/decisiones_del_grupo.md` |

La etapa 9 (despliegue) es la propia app: la pestaña 8 es su producto. Los informes `09_despliegue.md`, `informe_tecnico.md` e `integracion_main.md` **no**
tienen pestaña (ver Supuestos).

## Requisitos funcionales

- **FR-001**: La app MUST seguir en `app/streamlit_app.py` (mismo entrypoint) y MUST NOT cambiar `requirements.txt`.
- **FR-002**: Ninguna cifra MUST escribirse a mano en la app; todo número sale de `reports/*.md|json|csv` o `models/*` (principio VII).
- **FR-003**: Si falta un archivo, la pestaña MUST mostrar un aviso con su ruta y NOT fallar (las demás siguen).
- **FR-004**: La lógica reutilizable (leer informes, partir markdown en secciones, tarjetas de métricas, pendientes, formateo de números y segmentos) MUST vivir
  en `src/proyecto/reporting/`; `app/streamlit_app.py` solo dibuja (principio VI). Cada función nueva MUST tener al menos una prueba (principio IV).
- **FR-005**: El markdown de los archivos MUST dibujarse con `st.markdown` sin `unsafe_allow_html`.
- **FR-006**: La app MUST NOT leer `.env`, consultar Databricks ni importar `mlflow`, `optuna` o `shap` (principio V y restricciones).
- **FR-007**: Las rutas MUST ser relativas al repositorio (`Path(__file__)`); los archivos MUST estar versionados (ninguno ignorado por Git).
- **FR-008**: La lectura de archivos MUST usar `st.cache_data` y el modelo `st.cache_resource` (carga rápida).
- **FR-009**: El formulario MUST conservar campos, validación, "(no sé)" y el resultado `LLAMAR`/`NO LLAMAR`; el primer botón de la página MUST ser **Evaluar** y
  el primer `st.metric` MUST ser "Resultado sugerido" (las tarjetas de la pestaña 5 no usan `st.metric` para no alterar ese orden).
- **FR-010**: Los avisos de honestidad MUST extraerse de los archivos (secciones y viñetas), no reescribirse.

## Casos límite

- **Informe vacío o sin la sección esperada** (por ejemplo, alguien renombra "3.1"): se muestra el informe completo y un aviso; no hay excepción.
- **JSON sin `prueba`** o con claves faltantes: se muestran solo las tarjetas que se pueden armar; nunca se rellenan con ceros.
- **CSV de segmentos con una variable nueva**: se agrupa por la columna `variable` sin lista fija de variables.
- **`models/model.joblib` ausente en la nube**: la pestaña 8 muestra el error de siempre; las pestañas 1 a 7 siguen sirviendo.
- **Archivos grandes**: `06_mlflow_runs.csv` y `05_torneo_folds.csv` no se leen (no hacen falta).

## Riesgos que se vigilan

- **Fuga de secretos**: la app no toca `.env`; se revisa con `git grep` que ningún cambio contenga token, correo ni dirección del workspace.
- **Reescribir las advertencias**: se evita extrayéndolas por título de sección; una prueba falla si la sección deja de existir.
- **Despliegue**: `streamlit==1.66.0` ya está en `requirements.txt`; no se usan funciones de versiones posteriores.
- **Interfaz recargada**: informes largos; se usan subpestañas y desplegables, y se verifica con capturas reales.

## Supuestos *(decisiones tomadas sin consultar; cámbialas si no te sirven)*

1. **Ocho pestañas, tal como se propuso.** Siguen el orden de las etapas (1, 2, 4, 5-6, 7, 8, transversales y 9). Las etapas 5 y 6 comparten pestaña
   (subpestañas) porque la 6 es la continuación de la 5. La etapa 3 (preprocesamiento) se cuenta dentro de "Datos y EDA" porque el informe del EDA
   incluye las decisiones de limpieza.
2. **Los avisos van encima de las pestañas**, no solo en la 5 o la 7, para que no se pueda ver el modelo sin ver sus límites.
3. **Se extraen de `models/ficha_modelo.md`, sección "Límites y usos no recomendados"**, las viñetas "Atributos sensibles…" y "La prueba en el grupo…". Si no se encuentran,
   se muestra la sección completa. De `reports/prueba_abierta.txt` se muestra el texto entero. De las decisiones solo se cuenta cuántas pendientes siguen abiertas (las que no dicen `CERRADO`).
4. **Tarjetas de la pestaña 5 sin `st.metric`** (contenedor con borde, título pequeño y valor), para que `tests/test_app.py` siga pasando sin tocarse.
5. **Formato numérico español** (coma decimal, 4 decimales el costo, 1 decimal los porcentajes), calculado con una función; no se copian textos de cifras.
6. **La tabla de segmentos se muestra por variable** (género, edad, región) con encabezados en español; los nombres de columnas del CSV no se modifican en el archivo.
7. **No se muestran** `09_despliegue.md`, `informe_tecnico.md` ni `integracion_main.md`: son documentos de proceso o duplican los otros. Se pueden añadir como pestaña 9 si el grupo lo pide.
8. **Las imágenes** se leen del repositorio con `st.image`; los informes no las referencian, así que se muestran junto al título de su sección en la app.
9. **Sin widgets nuevos fuera del formulario** (ni filtros ni botones): hace la app más rápida y deja intactas las pruebas con `AppTest`.
10. **El título de la página** sigue saliendo de `schema["app_title"]`; si falta el esquema, se usa un título genérico.

## Clarificaciones *(sesión 2026-11-06, sin usuario disponible: se decidió con criterio)*

- ¿Se agrega una pestaña para la etapa 3 y otra para la 9? → No: la 3 se explica en el EDA y la 9 es la pestaña "Probar el modelo" (Supuesto 1).
- ¿Dónde van las advertencias de honestidad? → Encima de las pestañas, extraídas de los archivos (Supuestos 2 y 3).
- ¿Se pueden usar `st.metric` en las tarjetas? → No, para no alterar `at.metric[0]` de las pruebas existentes (Supuesto 4).
- ¿Se agregan filtros o botones? → No (Supuesto 9).
- ¿Se leen los CSV grandes de MLflow/pliegues? → No (casos límite).

## Fuera de alcance

Reentrenar o recalcular métricas; tocar `models/*.joblib`, `models/input_schema.json`, `data/`, `notebooks/` o el contenido de `reports/`; cambiar `requirements.txt`;
consultar Databricks; autenticación; edición de los informes desde la app; gráficos nuevos (solo las imágenes que ya existen).

## Criterios de aceptación

1. Las 8 pestañas cargan sin excepción (`AppTest`), y cada una muestra contenido tomado de su archivo.
2. Cada tarjeta de métrica coincide con `07_metricas_test.json` (prueba automática).
3. Los avisos de honestidad se ven sobre las pestañas y su texto aparece literalmente en los archivos fuente (prueba automática).
4. Con un archivo ausente, la pestaña muestra un aviso y la app no falla (prueba automática con una raíz temporal).
5. `tests/test_app.py` original pasa sin cambios y la suite completa queda en verde (124 pruebas previas más las nuevas).
6. `git check-ignore` no marca ningún archivo que la app lee; `git grep` de secretos sale vacío.
7. Capturas reales de la app local revisadas: sin texto cortado, tablas rotas ni imágenes faltantes.
