# Registro de decisiones del grupo

> Revisión de todas las marcas **[DECIDE EL GRUPO]** de los notebooks 01 a 06, las especificaciones y los informes, completadas con lo medido en el proyecto.
> **Qué se hizo y qué no:** lo que se podía resolver con evidencia del proyecto se cerró con su cifra. Lo que depende de un dato que solo tiene la aseguradora (margen por venta, capacidad de llamadas, criterios legales) **no se inventó**: queda pendiente, con el valor de trabajo que se está usando y cuánto cambiaría el resultado si el dato real fuera otro.

## Cómo leer los estados

| Estado | Qué significa |
|---|---|
| **[DECIDIDO]** | Se resolvió con evidencia de este proyecto. Se puede cambiar, pero hace falta evidencia nueva. |
| **[ADOPTADO]** | Propuesta que ya se aplicó y funcionó, o regla por defecto vigente hasta que el grupo diga lo contrario. |
| **[PENDIENTE: dato externo]** | No se puede resolver con estos datos. Tiene valor de trabajo y responsable. |
| **[REEMPLAZADO]** | Dejó de estar vigente por una decisión posterior, que se indica. Se conserva el texto original como historia. |

## Resumen

- **15 decisiones** (D01 a D15; D12 y D14 **reemplazadas** por D15) y **12 pendientes** (P01 a P12; **P12 cerrada**). **El 2026-11-06 el grupo adoptó la opción recomendada de P01, P02, P03, P04, P06, P08, P09 y P11 como supuestos declarados**: siguen marcadas «por confirmar» porque ninguna tiene aún respuesta de la aseguradora, de Legal ni del instructor. Siguen abiertas P05 (licencia), P07 (roles y nombre de la startup) y P10 (aprobaciones).
- **Actualizado el 2026-11-06 (`specs/007-integracion-main`):** el grupo decidió que el **modelo final es el de la rama de Andiry**, porque debe incluir las **5 variables nuevas** (D15). El código oficial de `src/` pasa a ser el de esa rama. **Las cifras de D01 a D11 y de P01 a P04 se midieron con el código anterior de `main`** (etapas 4 a 6 de la compañera) y se conservan como historia; las del modelo final están en `reports/04_features.md` a `reports/07_validacion.md` y en `models/ficha_modelo.md`. Detalle de la integración: `reports/integracion_main.md`.
- **Actualizado el 2026-11-05:** el grupo decidió **eliminar `Policy_Sales_Channel`** (posible fuga) y **conservar `Gender`**; las etapas 3 a 6 se reejecutaron y las cifras de abajo son las nuevas.
- **Ninguna de las pendientes bloquea el modelado.** Solo **P03** (si se exige explicar cada llamada) debe quedar resuelta **antes de abrir la prueba cerrada** en la etapa 7, porque decide cuál modelo se confirma.
- **La que más mueve las cifras es P01 (el valor de R)**, y aun así las etapas 5 y 6 mostraron que **no cambia los finalistas ni el umbral de forma relevante** (R entre 2 y 12).

---

## A. Decisiones cerradas o adoptadas con evidencia

| ID | Decisión | Estado | Evidencia | Dónde está |
|---|---|---|---|---|
| **D01** | **Métrica principal:** PR-AUC para elegir variables y modelos; **costo por cliente** (R = 5) como métrica de negocio | **[DECIDIDO]** | Usadas en las etapas 4 a 6 con resultados coherentes: LightGBM y XGBoost son 1.º y 2.º en costo y en PR-AUC. La PR-AUC no depende de R; el costo sí | `especificacion-proyecto.md`, nb 01, 04, 05, 06 |
| **D02** | **Métricas secundarias:** recall y *lift* en el 20 % mejor puntuado, ROC-AUC, log loss, Brier, costo con R = 5 y revisión por grupos | **[DECIDIDO]** | Calculadas en cada pliegue (`technical_metrics`); explicaron por qué el bosque pierde pese a su ROC-AUC (calibración) | nb 05 §5, `reports/05_torneo.md` |
| **D03** | **Qué resultado hace que el negocio diga "sirve":** costo por cliente menor que el de la regla "llamar si hubo daño" | **[DECIDIDO]** | **Cumplido en validación cruzada:** LightGBM 0,3326 frente a 0,398 (**16,4 % menos**, ≈ 6.500 unidades por 100.000 clientes). Se confirma con la prueba cerrada en la etapa 7 | nb 01 §4, nb 05 §8 |
| **D04** | **Reglas R1 a R5** para agregar o retirar variables (evidencia, disponibilidad, complejidad, retiro, equidad) | **[ADOPTADO]** | Aplicadas sin cambios en las etapas 4 a 6: evitaron adoptar 4 ideas sin valor y 6 variables derivadas sin aporte; justificaron retirar `Vintage` y `Driving_License` sin costo medible, y conservar la prima (quitarla empeora 1,5 veces el ruido). `Gender` también se podía retirar sin costo, pero el grupo decidió conservarla (D12) | nb 04 §1.2, `reports/04_features.md` |
| **D05** | **Criterios para elegir finalistas, en orden:** consistencia → costo → ranking → tiempo → explicabilidad | **[ADOPTADO]** | Aplicados en el torneo: LightGBM y regresión pasan; XGBoost se descarta (empate práctico, casi el doble de lento); bosque y árbol se descartan | nb 05 §1 y §10, `reports/05_torneo.md` |
| **D06** | **Regla del intervalo:** usar parámetros optimizados solo si todo el intervalo del 95 % está por debajo de cero en clientes reservados | **[ADOPTADO]** | Evitó prometer una mejora falsa: la búsqueda vio 0,3331 → 0,3318 en LightGBM, pero en reservados la diferencia fue -0,0002, intervalo [-0,0021; +0,0018]; en la regresión, -0,0006, intervalo [-0,0020; +0,0009] | nb 06 §1 y §6, `reports/06_optimizacion.md` |
| **D07** | **Umbral para agrupar regiones raras:** menos de 100 clientes pasan a "otros" | **[DECIDIDO]** | Idea 8 (etapa 4): agrupar es neutral (0,00 veces el ruido) porque hoy ninguna región tiene menos de 100 clientes; queda como protección ante regiones nuevas. El canal de venta ya no entra al modelo (D13) | nb 02, nb 04, `src/proyecto/features/engineering.py` |
| **D08** | **Operar por umbral `1 ÷ (R + 1)` (16,7 %)**, dimensionando al equipo para ≈ 36 % de la base | **[DECIDIDO]** | Mínimo empírico 17,5 % (costo 0,3330 frente a 0,3331); banda de 15 % a 18 % varía menos de 0,001; en reservados mover el umbral da +0,0011, intervalo [-0,0004; +0,0027]. El umbral equivale a llamar al 36,0 % | nb 06 §7, `reports/06_best_params.json` |
| **D09** | **Escala de reporte:** todo se expresa por 100.000 clientes | **[DECIDIDO]** | Es una convención para comparar, **no un pronóstico** de campaña. Cambiar la escala multiplica las unidades pero no cambia ninguna conclusión | nb 04, 05, 06 |
| **D10** | **Modelo para la validación final:** LightGBM como **principal**, regresión logística como **alternativa explicable**. Si se exige explicar cada llamada (P03), se despliega la regresión | **[ADOPTADO]** por defecto | En reservados la regresión cuesta +0,0028 más, intervalo [+0,0002; +0,0055]: LightGBM es mejor con confianza del 95 %, por poco; la diferencia (≈ 280 unidades por 100.000, menos del 1 %) no justifica perder la explicación si se necesita | nb 05 §10, nb 06 §8 y §11, `reports/06_optimizacion.md` |
| **D11** | **Criterio de reemplazo del modelo:** reentrenar si la tasa real de aceptación se aleja de la predicha más de un 10 % relativo durante 2 campañas | **[ADOPTADO]** por defecto | Propuesta de monitoreo; el modelo está calibrado en validación (diferencia máxima 0,010 en LightGBM). El 10 % y las 2 campañas son un punto de partida: se ajustan con datos reales de producción | nb 05 §10.1, nb 06 §11.2 |
| **D12** | **Variables retiradas del modelo:** `Vintage`, `Driving_License` (más `id`). **`Gender` se conserva** por decisión del grupo (2026-11-05) | ~~[DECIDIDO por el grupo]~~ **[REEMPLAZADO 2026-11-06] por D15**: el modelo final conserva `Vintage` y `Driving_License`; `Gender` sigue | Quitar `Vintage` y la licencia no cambia el costo (0,3322 frente a 0,3326); quitar además `Gender` tampoco (0,3327), así que conservarla no cuesta nada medible. La app pide 7 datos. Como el género entra directo al modelo, se audita por género y edad en la etapa 7 y Legal debe aprobar su uso | nb 04 §9, `reports/04_features.md` |
| **D13** | **`Policy_Sales_Channel` se elimina** en la limpieza (decisión 8 del EDA: posible fuga, el canal de contacto puede no conocerse antes de decidir) | **[DECIDIDO por el grupo]** | Cuesta ≈ 0,008 por cliente (LightGBM 0,3326 sin canal frente a 0,3245 con canal; ≈ 800 unidades por 100.000 clientes, unas 3 veces el ruido). Si la aseguradora confirma que el canal se conoce al llamar, se puede volver a medir con y sin (P11) | `src/proyecto/data/cleaning.py`, nb 03, nb 04 §8 |
| **D14** | **Mantener los parámetros de partida de LightGBM** (no adoptar los de la búsqueda de Optuna de Andiry) y dejar su mejora como siguiente paso | ~~[ADOPTADO]~~ **[REEMPLAZADO 2026-11-06] por D15**: el modelo final usa los parámetros de Optuna (ensayo #13) | Su búsqueda (40 ensayos) baja el costo de 0,3327 a 0,3303 (IC 95 % [−0,0042; −0,0006]), ≈ 240 unidades por 100.000 clientes, del orden del ruido (≈ 230). Se calculó sobre un entrenamiento con 649 clientes menos (P12) y la prueba cerrada ya se abrió con los parámetros de partida (2026-11-05 19:09), así que cambiarlos obligaría a reentrenar, volver a registrar en Databricks y declarar un cambio posterior a la prueba | `reports/06_optimizacion.md`, `specs/004-optimizacion/` |
| **D15** | **Modelo final = el de la rama de Andiry:** LightGBM con las **5 variables nuevas** (`uninsured_with_damage`, `damage_x_vehicle_age`, `is_young_customer`, `age_peak_distance`, `premium_per_age`), sin `Policy_Sales_Channel` (D13), con `Gender`, `Vintage` y `Driving_License`, parámetros de Optuna (ensayo #13). **Reemplaza** a D12, a D14 y a la conclusión de la etapa 4 de `main` ("ninguna variable nueva mejora al modelo", que se refería a **otras** 5 ideas, distintas de estas) | **[DECIDIDO por el grupo 2026-11-06]** | Motivo: el grupo exige que el modelo final incluya las variables nuevas. **No se eligió comparando cifras de prueba**: la prueba ya se había abierto con los dos modelos (19:09 y 20:43 del 2026-11-05) y eso se declara en `reports/07_validacion.md` §3.1. En la prueba: costo 0,3312, IC 95 % [0,3263; 0,3364]; frente a la regla de negocio, −0,0408, IC 95 % [−0,0453; −0,0362] | `reports/07_validacion.md`, `models/ficha_modelo.md`, `specs/007-integracion-main/` |

---

## B. Pendientes de dato externo

> **Bloquea el modelado:** ninguna. **Bloquea abrir la prueba cerrada:** solo P03.

### P01 · Valor de R (cuánto cuesta no llamar a un comprador frente a una llamada inútil) — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se mantiene **R = 5** como supuesto declarado (umbral 16,7 %). Si el instructor o la aseguradora dan otro valor, se usa ese y se repiten los cuadernos 05 a 07.

| | |
|---|---|
| **Qué falta** | El margen de una venta de seguro de vehículo y el costo de una llamada |
| **Quién lo cierra** | Negocio / Finanzas de la aseguradora |
| **Cómo se calcula** | R = margen por venta ÷ costo de una llamada |
| **Valor de trabajo vigente** | **R = 5** (hipótesis; umbral 16,7 %) |
| **Por qué no se pudo resolver** | Es un dato económico de la aseguradora; no sale de ningún dato del dataset |
| **Qué cambia si es otro** | **Los finalistas no cambian** con R entre 2 y 12 (LightGBM y XGBoost siempre 1.º y 2.º). Cambia el umbral (R = 3 → 25 %; R = 4 → 20 %; R = 6 → 14,3 %; R = 8 → 11,1 %) y el costo absoluto. Usar por error el umbral de R = 4 o R = 6 cuando fuera R = 5 sube el costo a ≈ 0,331 o ≈ 0,328, a menos de 0,005 del mínimo. Con R ≤ 3, la regla "llamar si hubo daño" deja de llamar |
| **Dónde se actualiza** | `COST_MATRIX` en `src/proyecto/config.py` (antes `COST_FALSE_NEGATIVE` en `metrics.py`, que se quitó en la integración del 2026-11-06); un R distinto obliga a decidir el umbral de nuevo **con validación**, no con la prueba |

### P02 · Capacidad real de llamadas del equipo comercial — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se **opera por umbral** (≈ 36 % de la base) y se presenta la tabla de costo por capacidad (20 %, 30 %, 35 %, 40 %, 50 %). Limitar a 20 % cuesta ≈ 7.000 unidades más por 100.000 clientes (cifra de la versión anterior de `main`).

| | |
|---|---|
| **Qué falta** | Cuántos clientes puede llamar el equipo por campaña |
| **Quién lo cierra** | Ventas / Operaciones |
| **Valor de trabajo vigente** | Operar por umbral, dimensionando para **≈ 36 %** de la base |
| **Qué cambia si es otra** | Cada capacidad tiene un costo medido (por 100.000 clientes): **20 %** → 40.333 unidades y 55,7 % de los compradores encontrados; **30 %** → 34.592 y 77,1 %; **35 %** → **33.307** y 85,6 %; **40 %** → 33.682 y 91,9 %; **50 %** → 38.578. **Limitar a 20 % cuesta ≈ 7.000 unidades más** y pierde el 44 % de los compradores. Entre 30 % y 40 % el costo es casi plano |

### P03 · ¿Se exige explicar cada llamada? (el único que debe cerrarse antes de la etapa 7) — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** **LightGBM** es el modelo principal (modelo final, D15). Si Legal o el instructor exigen explicar cada llamada, el modelo desplegado pasa a la regresión logística (costaba ≈ 0,8 % más en la versión anterior; hay que remedirlo con el modelo final).

| | |
|---|---|
| **Qué falta** | Si la regulación, el área legal o el negocio exigen una explicación individual por cliente |
| **Quién lo cierra** | Legal + Negocio |
| **Valor de trabajo vigente** | **LightGBM principal; regresión como alternativa lista** (D10) |
| **Qué cambia si se exige** | El modelo desplegado pasa a ser la regresión logística. Costo: **≈ 260 a 280 unidades por 100.000 clientes** (≈ 0,8 % del costo total). La regresión se explica con una fórmula: quien ya tiene seguro tiene un 98 % menos de posibilidades de comprar (razón de odds 0,016) y quien tuvo un daño tiene 7,3 veces más |
| **Por qué debe cerrarse antes de la etapa 7** | La prueba cerrada se abre **una sola vez** para confirmar la cifra del modelo elegido; elegir el modelo **después** de verla la invalidaría |

### P04 · Piso de contacto para clientes de 20-25 años y de 66 o más — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se **mantiene el modelo** (prioriza por rentabilidad esperada), se documenta que casi no llama a los clientes más jóvenes ni a los mayores (ver `reports/07_validacion.md`) y se recomienda al negocio una **oferta distinta** para esos grupos, no más llamadas. No se fija un mínimo de contacto.

| | |
|---|---|
| **Qué falta** | Una política comercial: ¿hay un mínimo de contacto o una oferta distinta para estos grupos? |
| **Quién lo cierra** | Comercial + Legal |
| **Valor de trabajo vigente** | Ninguno: el modelo prioriza por rentabilidad esperada |
| **Evidencia** | LightGBM llama solo al **5,6 %** de los de 20-25 años (recall 33 %) y al **15,6 %** de los de 66 o más (recall 35 %); en el entrenamiento **2.157 compradores jóvenes y 1.225 mayores no son llamados**. No es un fallo del modelo: estos grupos compran poco (3,5 % y 8,4 %) y llamarlos no compensa con R = 5 |
| **Qué se mide después** | La auditoría completa por género y edad con la prueba cerrada, en la etapa 7. Como `Gender` entra al modelo (D12), Legal debe aprobar su uso |

### P11 · ¿El canal de venta se conoce antes de decidir a quién llamar? — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se **sigue sin el canal de venta** (decisión conservadora, D13). Solo cambia si la aseguradora confirma que se conoce antes de llamar; entonces se vuelve a medir con y sin canal.

| | |
|---|---|
| **Qué falta** | Confirmar con la aseguradora si `Policy_Sales_Channel` está disponible **antes** de la llamada o es resultado del contacto |
| **Quién lo cierra** | Negocio / Ventas |
| **Valor de trabajo vigente** | Se **elimina** (D13) |
| **Qué cambia si se conoce** | Se puede volver a medir con y sin canal: con él LightGBM costaba 0,3245 en validación cruzada frente a 0,3326 sin él (≈ 800 unidades por 100.000 clientes) |

### P12 · ¿Por qué el entrenamiento de Andiry tiene 649 clientes menos? — **[CERRADO 2026-11-06]**

> **Respuesta:** son **perfiles repetidos** (misma fila y misma respuesta con distinto `id`) que aparecen al eliminar `Policy_Sales_Channel`. La limpieza de la rama los quita **solo del entrenamiento**, después de partir (`drop_duplicate_rows` en `src/proyecto/data/split.py`); la prueba queda tal como llega. Con D15, el entrenamiento oficial es el de 304.238 clientes. Lo que sigue es el texto original.

| | |
|---|---|
| **Qué falta** | Confirmar con Andiry por qué su `train.parquet` tiene 304.238 filas y el de esta rama 304.887 |
| **Quién lo cierra** | Andiry y el grupo |
| **Qué se sabe** | Las 649 filas que le faltan tienen **todas la prima mínima de 2.630** (tasa de compra 8,2 % frente a 12,3 % del total); la prueba de 76.222 clientes es idéntica en ambas versiones |
| **Valor de trabajo vigente** | Se usan los 304.887 clientes (no se quitó ninguna fila: la prima 2.630 es un mínimo real del producto, decisión 4 del EDA) |
| **Qué cambia si se quitan** | Habría que repetir las etapas 3 a 9 y las cifras de validación cambiarían; la comparación con su búsqueda de Optuna solo es válida con los mismos datos |

### P05 · Fuente, enlace y licencia del dataset

> **Intento de cierre 2026-11-06:** se consultó la página de Kaggle del conjunto y **no se pudo leer el campo *License***; solo hay una mención de terceros (GPL-2) sin verificar. **Sigue pendiente:** una persona del grupo debe abrir la página en el navegador y copiar el campo *License*. Si no permite redistribuir, hay que quitar `dataset.csv` y los Parquet del repositorio público.

| | |
|---|---|
| **Qué falta** | Confirmar el enlace del conjunto, su autor y su licencia |
| **Quién lo cierra** | El grupo (revisando la página del conjunto en Kaggle) |
| **Qué se verificó** | El esquema y el tamaño (381.109 filas × 12 columnas, objetivo `Response`) coinciden con el conjunto de Kaggle *Health Insurance Cross Sell Prediction* |
| **Qué no se pudo verificar** | **La licencia.** La búsqueda no llegó a la página primaria; solo una referencia de terceros menciona GPL-2, **sin confirmar**. No se afirma |
| **Por qué importa** | El repositorio de la compañera ya contiene `dataset.csv`: confirmar la licencia antes de mantenerlo en un repositorio público |

### P06 · El caso de negocio en palabras de la aseguradora — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se **mantiene la hipótesis** del caso (decide el equipo comercial; pesa más no llamar a un interesado) y se declara como supuesto hasta que el instructor apruebe la ficha de caso.

| | |
|---|---|
| **Qué falta** | Confirmar la pregunta de negocio, quién decide y con qué información, **cuál error pesa más** y qué se hace hoy sin el modelo |
| **Quién lo cierra** | Rol *Negocio* del grupo |
| **Valor de trabajo vigente** | "¿A qué clientes con seguro de salud conviene ofrecerles un seguro de vehículo?"; decide el equipo comercial; pesa más no llamar a un comprador (R = 5) |
| **Qué ya se comprobó** | Solo el 12,26 % acepta, así que conviene priorizar: con R entre 2 y 12 todos los modelos superan a las líneas base, y el segmento "sin seguro y con daño" concentra el 97,7 % de los compradores en el 48 % de la lista |

### P07 · Integrantes, roles, nombre de la startup y repositorio

| | |
|---|---|
| **Qué falta** | El **nombre de la startup**. **Roles:** el grupo indicó (2026-11-06) que los cinco integrantes trabajaron **por igual y en conjunto** en todas las etapas, y así quedó en el `README.md` y la especificación; los commits del repositorio los hicieron Ricardo y Jessica Andiry. **Ya está:** el nombre del proyecto («Venta cruzada inteligente: predicción del interés en seguro de vehículo»), los 5 integrantes y el repositorio (https://github.com/andiryospina/proyecto_venta_cruzada_seguro) |
| **Quién lo cierra** | El grupo |
| **Dónde va** | `especificacion-proyecto.md` §1, `README.md` e `informe_tecnico.md` |

### P08 · Qué datos nuevos pedir a la aseguradora — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se adoptan como **siguientes pasos** (no como compromiso) los dos primeros datos de la lista: historial de contactos y vencimiento del seguro de vehículo actual.

| | |
|---|---|
| **Qué falta** | Decidir cuáles de estos datos vale la pena pedir y cuáles existen: 1) historial de contactos, 2) vencimiento del seguro de vehículo actual, 3) tiempo desde el último siniestro y su monto, 4) número de vehículos y pólizas del hogar, 5) canal y horario preferidos de contacto, 6) ingreso (solo con revisión legal) |
| **Quién lo cierra** | Negocio + TI de la aseguradora |
| **Por qué** | La segunda ronda de variables mostró que **el techo del modelo está en los datos**: 6 variables derivadas no mejoraron nada, y optimizar parámetros tampoco |
| **Cómo se mediría** | Se agrega cada dato y se repite el experimento de la etapa 4 con la misma regla (mejora sobre ruido) |

### P09 · Por qué el daño del vehículo lleva a comprar — **[ADOPTADO 2026-11-06: supuesto del grupo, por confirmar]**

> **Adoptado el 2026-11-06 (opción recomendada, de acuerdo el grupo):** Se deja como **hipótesis**: el texto dice que el daño «se asocia con» comprar, no que lo cause. No cambia el modelo.

| | |
|---|---|
| **Qué falta** | Validar con el negocio la explicación (el daño hace sentir la necesidad del seguro) |
| **Por qué no se resuelve con los datos** | Los datos muestran la **asociación** (23,8 % frente a 0,5 % de aceptación), no la causa |
| **Impacto** | Ninguno en el modelo; sí en el discurso comercial |

### P10 · Aprobaciones formales

| | |
|---|---|
| **Qué falta** | (1) **Ficha de caso:** pasar de `borrador` a `aprobada` (la aprueba el instructor); (2) **especificaciones 02 y 03:** el grupo las revisa y cambia su estado a `cerrada`; (3) **revisión del código** con `material-del-curso/kit/checklist-revision-ia.md`, de modo que cada integrante pueda explicar una función |
| **Quién lo cierra** | Instructor y grupo |
| **Por qué no se hizo** | Son aprobaciones humanas; no se pueden dar por hechas desde el repositorio |

---

## C. Hoja de cierre (para firmar)

| ID | Responsable | Decisión final | Fecha |
|---|---|---|---|
| P01 · R | Negocio / Finanzas | Adoptado como supuesto del grupo: Supuesto R = 5; sin confirmación externa | 2026-11-06 |
| P02 · Capacidad | Ventas | Adoptado como supuesto del grupo: Operar por umbral; capacidad real sin confirmar | 2026-11-06 |
| P03 · Explicación individual | Legal + Negocio | Adoptado como supuesto del grupo: LightGBM principal; regresión si se exige explicación | 2026-11-06 |
| P04 · Piso de contacto | Comercial + Legal | Adoptado como supuesto del grupo: Sin piso de contacto; recomendación documentada | 2026-11-06 |
| P05 · Fuente y licencia | Grupo | | |
| P06 · Caso de negocio | Negocio | Adoptado como supuesto del grupo: Hipótesis del caso; falta aprobar la ficha | 2026-11-06 |
| P07 · Roles y nombre de la startup | Grupo | | |
| P08 · Datos nuevos | Negocio + TI | Adoptado como supuesto del grupo: Siguientes pasos: historial de contactos y vencimiento del seguro | 2026-11-06 |
| P09 · Hipótesis del daño | Negocio | Adoptado como supuesto del grupo: Hipótesis; se redacta como asociación, no como causa | 2026-11-06 |
| P10 · Aprobaciones | Instructor y grupo | | |
| P11 · Canal de venta | Negocio / Ventas | Adoptado como supuesto del grupo: Sin canal de venta; falta confirmación | 2026-11-06 |
| P12 · 649 clientes de prima 2.630 | Andiry y el grupo | Cerrado: perfiles repetidos al quitar el canal; se quitan del entrenamiento (D15) | 2026-11-06 |
