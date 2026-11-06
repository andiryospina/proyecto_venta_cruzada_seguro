# Registro de decisiones del grupo

> Revisión de todas las marcas **[DECIDE EL GRUPO]** de los notebooks 01 a 06, las especificaciones y los informes, completadas con lo medido en el proyecto.
> **Qué se hizo y qué no:** lo que se podía resolver con evidencia del proyecto se cerró con su cifra. Lo que depende de un dato que solo tiene la aseguradora (margen por venta, capacidad de llamadas, criterios legales) **no se inventó**: queda pendiente, con el valor de trabajo que se está usando y cuánto cambiaría el resultado si el dato real fuera otro.

## Cómo leer los estados

| Estado | Qué significa |
|---|---|
| **[DECIDIDO]** | Se resolvió con evidencia de este proyecto. Se puede cambiar, pero hace falta evidencia nueva. |
| **[ADOPTADO]** | Propuesta que ya se aplicó y funcionó, o regla por defecto vigente hasta que el grupo diga lo contrario. |
| **[PENDIENTE: dato externo]** | No se puede resolver con estos datos. Tiene valor de trabajo y responsable. |

## Resumen

- **13 decisiones cerradas o adoptadas** (D01 a D13) y **11 pendientes de dato externo** (P01 a P11).
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
| **D12** | **Variables retiradas del modelo:** `Vintage`, `Driving_License` (más `id`). **`Gender` se conserva** por decisión del grupo (2026-11-05) | **[DECIDIDO por el grupo]** | Quitar `Vintage` y la licencia no cambia el costo (0,3322 frente a 0,3326); quitar además `Gender` tampoco (0,3327), así que conservarla no cuesta nada medible. La app pide 7 datos. Como el género entra directo al modelo, se audita por género y edad en la etapa 7 y Legal debe aprobar su uso | nb 04 §9, `reports/04_features.md` |
| **D13** | **`Policy_Sales_Channel` se elimina** en la limpieza (decisión 8 del EDA: posible fuga, el canal de contacto puede no conocerse antes de decidir) | **[DECIDIDO por el grupo]** | Cuesta ≈ 0,008 por cliente (LightGBM 0,3326 sin canal frente a 0,3245 con canal; ≈ 800 unidades por 100.000 clientes, unas 3 veces el ruido). Si la aseguradora confirma que el canal se conoce al llamar, se puede volver a medir con y sin (P11) | `src/proyecto/data/cleaning.py`, nb 03, nb 04 §8 |

---

## B. Pendientes de dato externo

> **Bloquea el modelado:** ninguna. **Bloquea abrir la prueba cerrada:** solo P03.

### P01 · Valor de R (cuánto cuesta no llamar a un comprador frente a una llamada inútil)

| | |
|---|---|
| **Qué falta** | El margen de una venta de seguro de vehículo y el costo de una llamada |
| **Quién lo cierra** | Negocio / Finanzas de la aseguradora |
| **Cómo se calcula** | R = margen por venta ÷ costo de una llamada |
| **Valor de trabajo vigente** | **R = 5** (hipótesis; umbral 16,7 %) |
| **Por qué no se pudo resolver** | Es un dato económico de la aseguradora; no sale de ningún dato del dataset |
| **Qué cambia si es otro** | **Los finalistas no cambian** con R entre 2 y 12 (LightGBM y XGBoost siempre 1.º y 2.º). Cambia el umbral (R = 3 → 25 %; R = 4 → 20 %; R = 6 → 14,3 %; R = 8 → 11,1 %) y el costo absoluto. Usar por error el umbral de R = 4 o R = 6 cuando fuera R = 5 sube el costo a ≈ 0,331 o ≈ 0,328, a menos de 0,005 del mínimo. Con R ≤ 3, la regla "llamar si hubo daño" deja de llamar |
| **Dónde se actualiza** | Constante `COST_FALSE_NEGATIVE` en `src/proyecto/models/metrics.py` y volver a ejecutar los notebooks 05 y 06 |

### P02 · Capacidad real de llamadas del equipo comercial

| | |
|---|---|
| **Qué falta** | Cuántos clientes puede llamar el equipo por campaña |
| **Quién lo cierra** | Ventas / Operaciones |
| **Valor de trabajo vigente** | Operar por umbral, dimensionando para **≈ 36 %** de la base |
| **Qué cambia si es otra** | Cada capacidad tiene un costo medido (por 100.000 clientes): **20 %** → 40.333 unidades y 55,7 % de los compradores encontrados; **30 %** → 34.592 y 77,1 %; **35 %** → **33.307** y 85,6 %; **40 %** → 33.682 y 91,9 %; **50 %** → 38.578. **Limitar a 20 % cuesta ≈ 7.000 unidades más** y pierde el 44 % de los compradores. Entre 30 % y 40 % el costo es casi plano |

### P03 · ¿Se exige explicar cada llamada? (el único que debe cerrarse antes de la etapa 7)

| | |
|---|---|
| **Qué falta** | Si la regulación, el área legal o el negocio exigen una explicación individual por cliente |
| **Quién lo cierra** | Legal + Negocio |
| **Valor de trabajo vigente** | **LightGBM principal; regresión como alternativa lista** (D10) |
| **Qué cambia si se exige** | El modelo desplegado pasa a ser la regresión logística. Costo: **≈ 260 a 280 unidades por 100.000 clientes** (≈ 0,8 % del costo total). La regresión se explica con una fórmula: quien ya tiene seguro tiene un 98 % menos de posibilidades de comprar (razón de odds 0,016) y quien tuvo un daño tiene 7,3 veces más |
| **Por qué debe cerrarse antes de la etapa 7** | La prueba cerrada se abre **una sola vez** para confirmar la cifra del modelo elegido; elegir el modelo **después** de verla la invalidaría |

### P04 · Piso de contacto para clientes de 20-25 años y de 66 o más

| | |
|---|---|
| **Qué falta** | Una política comercial: ¿hay un mínimo de contacto o una oferta distinta para estos grupos? |
| **Quién lo cierra** | Comercial + Legal |
| **Valor de trabajo vigente** | Ninguno: el modelo prioriza por rentabilidad esperada |
| **Evidencia** | LightGBM llama solo al **5,6 %** de los de 20-25 años (recall 33 %) y al **15,6 %** de los de 66 o más (recall 35 %); en el entrenamiento **2.157 compradores jóvenes y 1.225 mayores no son llamados**. No es un fallo del modelo: estos grupos compran poco (3,5 % y 8,4 %) y llamarlos no compensa con R = 5 |
| **Qué se mide después** | La auditoría completa por género y edad con la prueba cerrada, en la etapa 7. Como `Gender` entra al modelo (D12), Legal debe aprobar su uso |

### P11 · ¿El canal de venta se conoce antes de decidir a quién llamar?

| | |
|---|---|
| **Qué falta** | Confirmar con la aseguradora si `Policy_Sales_Channel` está disponible **antes** de la llamada o es resultado del contacto |
| **Quién lo cierra** | Negocio / Ventas |
| **Valor de trabajo vigente** | Se **elimina** (D13) |
| **Qué cambia si se conoce** | Se puede volver a medir con y sin canal: con él LightGBM costaba 0,3245 en validación cruzada frente a 0,3326 sin él (≈ 800 unidades por 100.000 clientes) |

### P05 · Fuente, enlace y licencia del dataset

| | |
|---|---|
| **Qué falta** | Confirmar el enlace del conjunto, su autor y su licencia |
| **Quién lo cierra** | El grupo (revisando la página del conjunto en Kaggle) |
| **Qué se verificó** | El esquema y el tamaño (381.109 filas × 12 columnas, objetivo `Response`) coinciden con el conjunto de Kaggle *Health Insurance Cross Sell Prediction* |
| **Qué no se pudo verificar** | **La licencia.** La búsqueda no llegó a la página primaria; solo una referencia de terceros menciona GPL-2, **sin confirmar**. No se afirma |
| **Por qué importa** | El repositorio de la compañera ya contiene `dataset.csv`: confirmar la licencia antes de mantenerlo en un repositorio público |

### P06 · El caso de negocio en palabras de la aseguradora

| | |
|---|---|
| **Qué falta** | Confirmar la pregunta de negocio, quién decide y con qué información, **cuál error pesa más** y qué se hace hoy sin el modelo |
| **Quién lo cierra** | Rol *Negocio* del grupo |
| **Valor de trabajo vigente** | "¿A qué clientes con seguro de salud conviene ofrecerles un seguro de vehículo?"; decide el equipo comercial; pesa más no llamar a un comprador (R = 5) |
| **Qué ya se comprobó** | Solo el 12,26 % acepta, así que conviene priorizar: con R entre 2 y 12 todos los modelos superan a las líneas base, y el segmento "sin seguro y con daño" concentra el 97,7 % de los compradores en el 48 % de la lista |

### P07 · Integrantes, roles, nombre de la startup y repositorio

| | |
|---|---|
| **Qué falta** | Nombres, roles (datos, modelado, app, negocio), nombre de la startup y enlace del repositorio público |
| **Quién lo cierra** | El grupo |
| **Dónde va** | `especificacion-proyecto.md` §1 y `README.md` |

### P08 · Qué datos nuevos pedir a la aseguradora

| | |
|---|---|
| **Qué falta** | Decidir cuáles de estos datos vale la pena pedir y cuáles existen: 1) historial de contactos, 2) vencimiento del seguro de vehículo actual, 3) tiempo desde el último siniestro y su monto, 4) número de vehículos y pólizas del hogar, 5) canal y horario preferidos de contacto, 6) ingreso (solo con revisión legal) |
| **Quién lo cierra** | Negocio + TI de la aseguradora |
| **Por qué** | La segunda ronda de variables mostró que **el techo del modelo está en los datos**: 6 variables derivadas no mejoraron nada, y optimizar parámetros tampoco |
| **Cómo se mediría** | Se agrega cada dato y se repite el experimento de la etapa 4 con la misma regla (mejora sobre ruido) |

### P09 · Por qué el daño del vehículo lleva a comprar

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
| P01 · R | Negocio / Finanzas | | |
| P02 · Capacidad | Ventas | | |
| P03 · Explicación individual | Legal + Negocio | | |
| P04 · Piso de contacto | Comercial + Legal | | |
| P05 · Fuente y licencia | Grupo | | |
| P06 · Caso de negocio | Negocio | | |
| P07 · Integrantes y repositorio | Grupo | | |
| P08 · Datos nuevos | Negocio + TI | | |
| P09 · Hipótesis del daño | Negocio | | |
| P10 · Aprobaciones | Instructor y grupo | | |
| P11 · Canal de venta | Negocio / Ventas | | |
