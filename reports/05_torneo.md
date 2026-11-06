# Informe del torneo de modelos

> **BORRADOR para revisión del grupo.** Resultado de `notebooks/05_torneo.ipynb`, reejecutado el 2026-11-05 **sin `Policy_Sales_Channel` y con `Gender`**. El torneo **descarta**: elige 1-2 finalistas con evidencia, no un campeón definitivo.
> Todas las cifras son de **validación cruzada** sobre el entrenamiento; la prueba cerrada **no se abrió**. Tabla reproducible: `reports/05_torneo_tabla.csv`.
> Estados de decisión: **[DECIDIDO]** (resuelto con evidencia del proyecto), **[ADOPTADO]** (propuesta vigente por defecto hasta que el grupo diga lo contrario) o **[PENDIENTE: dato externo]** (no se puede resolver con estos datos); registro en `reports/decisiones_del_grupo.md`. Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2.

## Resumen para quien decide

- **LightGBM** tiene el menor costo: **0,3326** por cliente, frente a **0,398** de la regla "llamar si hubo daño" y **0,613** de no llamar a nadie. Ahorra **≈ 6.500 unidades de llamada por cada 100.000 clientes** (16,4 %) frente a la regla simple.
- **LightGBM y XGBoost empatan en la práctica** (diferencia 0,0004; +0,46 veces el ruido). Se elige LightGBM por ser casi el doble de rápido (2,5 s frente a 4,6 s).
- **La regresión logística**, el modelo explicable, cuesta **0,3352**: ≈ 260 unidades más por 100.000 clientes que LightGBM (≈ 0,8 % del costo), y **supera al bosque, al árbol y a las líneas base**.
- **Finalistas: LightGBM y regresión logística.**
- **Cuidado de equidad por edad:** con el umbral de decisión, el modelo casi no llama a los de 20-25 años ni a los de 66 o más (recall de 33 % y 35 %).
- **Eliminar el canal de venta tiene un precio:** con él, LightGBM costaba 0,3245; sin él, 0,3326 (≈ 800 unidades por 100.000 clientes).

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos:** 5 pliegues estratificados por `Response`, semilla 42, **los mismos de las etapas 3 y 4**. Un cliente por fila (`id` único), así que no hace falta partir por grupo. 304.887 clientes de entrenamiento.
- **Líneas base:** (1) **no llamar a nadie** (predice la proporción de compradores, 12,26 %): costo 0,613; (2) **la regla de negocio "llamar si hubo daño"** (aprende la tasa con y sin daño): costo 0,398. Ningún modelo real las pierde.
- **Métrica principal (la de negocio):** **costo promedio por cliente** con R = 5 (umbral 16,7 %), en unidades de llamada. Complemento que no depende de calibración: **costo si solo se llama al 20 % mejor puntuado**. **R = 5 es una hipótesis [PENDIENTE: dato externo · P01].**
- **Métricas técnicas:** ROC-AUC, PR-AUC, exactitud balanceada, precisión y recall por clase, F1 macro, log loss, Brier, recall y *lift* en el 20 % mejor puntuado.
- **Variables usadas** (decididas en `reports/04_features.md`): sin `Vintage` ni `Driving_License`; **con `Gender`**; sin `Policy_Sales_Channel` (eliminado en la limpieza); regiones raras agrupadas. La regresión recibe además **la edad como curva** (+6,8 veces el ruido en la etapa 4); los árboles no la necesitan.
- **Criterios de elección, en orden [ADOPTADO · D05]:** consistencia (gana en 4 de 5 pliegues y supera 1 vez el ruido) → costo → ranking sin depender del umbral → tiempo y simplicidad → explicabilidad (solo si la exige el negocio o el regulador).

## Tabla comparativa

> Media ± desviación entre pliegues. Ordenada por costo (menor es mejor).

| Modelo | Costo por cliente (± ruido) | Costo si solo se llama al 20 % | Unidades por 100.000 clientes | Segundos de ajuste |
|---|---|---|---|---|
| **LightGBM** | **0,3326** (± 0,0023) | 0,4028 | **33.260** | 2,5 |
| XGBoost | 0,3330 (± 0,0020) | 0,4016 | 33.304 | 4,6 |
| **Regresión logística** | 0,3352 (± 0,0027) | 0,4014 | 33.519 | 1,8 |
| Bosque aleatorio | 0,3375 (± 0,0031) | 0,4038 | 33.749 | 40,7 |
| Árbol de decisión | 0,3401 (± 0,0013) | 0,4225 | 34.012 | 1,1 |
| Línea base: llamar si hubo daño | 0,3980 (± 0,0023) | 0,5275 | 39.803 | 0,0 |
| Línea base: no llamar a nadie | 0,6128 | 0,6653 | 61.282 | 0,0 |

## Métricas técnicas

> Media entre pliegues. Las de ranking usan las probabilidades; las de decisión usan el umbral de 16,7 %. Clase de interés = compradores.

| Modelo | ROC-AUC | PR-AUC | Exactitud balanceada | Precisión (compradores) | Recall no compradores | Recall compradores | F1 macro | Log loss | Brier | Recall en el 20 % mejor |
|---|---|---|---|---|---|---|---|---|---|---|
| LightGBM | **0,850** | **0,349** | 0,791 | 0,296 | 0,709 | 0,874 | 0,631 | **0,268** | **0,088** | 55,8 % |
| XGBoost | 0,850 | 0,349 | 0,791 | 0,296 | 0,710 | 0,872 | 0,632 | 0,268 | 0,088 | 55,9 % |
| Regresión logística | 0,848 | 0,339 | 0,790 | 0,293 | 0,706 | 0,874 | 0,629 | 0,269 | 0,088 | 55,9 % |
| Bosque aleatorio | 0,848 | 0,343 | 0,792 | 0,286 | 0,686 | **0,899** | 0,620 | 0,271 | 0,088 | 55,6 % |
| Árbol de decisión | 0,838 | 0,311 | 0,782 | 0,299 | 0,726 | 0,837 | **0,636** | 0,272 | 0,089 | 53,1 % |
| Línea base: llamar si hubo daño | 0,770 | 0,235 | 0,770 | 0,238 | 0,561 | 0,979 | 0,550 | 0,293 | 0,094 | 38,8 % |
| Línea base: no llamar a nadie | 0,500 | 0,123 | 0,500 | 0,000 | 1,000 | 0,000 | 0,467 | 0,372 | 0,108 | 20,1 % |

## ¿Coinciden los rankings de negocio y técnico?

> Posición entre los **7 candidatos** (1 = mejor).

| Modelo | Costo (negocio) | Costo al 20 % | ROC-AUC | PR-AUC | F1 macro | Recall de compradores |
|---|---|---|---|---|---|---|
| LightGBM | 1 | 3 | 2 | 2 | 3 | 4 |
| XGBoost | 2 | 2 | 1 | 1 | 2 | 5 |
| Regresión logística | 3 | 1 | 4 | 4 | 4 | 3 |
| Bosque aleatorio | 4 | 4 | 3 | 3 | 5 | 2 |
| Árbol de decisión | 5 | 5 | 5 | 5 | 1 | 6 |

- **¿El mejor por costo también es el mejor por AUC?** Casi: LightGBM y XGBoost son 1.º y 2.º en costo, ROC-AUC y PR-AUC; el orden entre ellos varía en milésimas. El resultado **no depende de la librería**.
- **¿Hay modelos con AUC casi igual pero costo distinto?** **Sí: bosque aleatorio y regresión logística** (ROC-AUC 0,848 los dos; costo 0,3375 frente a 0,3352). **Deciden distinto:** el bosque contacta más clientes (38,6 % frente a 36,5 %), con más recall (89,9 % frente a 87,4 %) y menos precisión (28,6 % frente a 29,3 %), porque sus **probabilidades están peor calibradas**. La regla de llamar con probabilidad > 16,7 % solo es óptima si la probabilidad es fiel.
- **¿Hay alguna clase con recall casi nulo?** Solo la línea base "no llamar a nadie" (recall 0 de compradores, por construcción). Entre los modelos reales, el recall de los no compradores va de 69 % a 73 %: ninguno sacrifica una clase. La regla "llamar si hubo daño" llama al 50,5 % y su recall de no compradores es de solo 56 %: gasta llamadas.

**Calibración** (diferencia máxima entre probabilidad predicha y real en un decil): XGBoost 0,007 · LightGBM 0,010 · regresión 0,013 · **bosque 0,032**.

## Comparación pareada de los mejores

> Los 5 pliegues son los mismos para todos. "Diferencia / ruido" = diferencia media ÷ desviación de la diferencia pliegue a pliegue.

| Mejor | Contra | Métrica | Diferencia media | Pliegues que gana | Diferencia / ruido | Lectura |
|---|---|---|---|---|---|---|
| LightGBM | XGBoost | costo | +0,0004 | 4 de 5 | +0,46 | **Empate práctico** |
| LightGBM | XGBoost | PR-AUC | -0,0002 | 2 de 5 | -0,12 | Empate práctico |
| LightGBM | Regresión | costo | +0,0026 | **5 de 5** | +2,40 | Ventaja consistente, pequeña |
| LightGBM | Regresión | PR-AUC | +0,0100 | **5 de 5** | **+6,34** | Ventaja clara en ranking |
| LightGBM | Bosque | costo | +0,0049 | **5 de 5** | +2,91 | Ventaja clara |
| Regresión | Bosque | costo | +0,0023 | **5 de 5** | +0,94 | Un modelo simple le gana a 150 árboles, por poco |
| Regresión | Árbol | costo | +0,0049 | **5 de 5** | +1,82 | Ventaja clara |

## ¿Cuánto vale la diferencia?

- **Decisiones estimadas por campaña:** 100.000 clientes (escala de reporte, no un pronóstico) **[DECIDIDO · D09]**.
- **Ahorro frente a la línea base "llamar si hubo daño":** LightGBM **+6.543** unidades de llamada (16,4 %); regresión +6.285 (15,8 %).
- **Ahorro frente a "no llamar a nadie":** LightGBM +28.022.
- **Diferencia entre el mejor y el siguiente:** LightGBM frente a XGBoost, 40 unidades; frente a la regresión, ≈ 260 unidades (≈ 0,8 % del costo total). El ruido del costo es ≈ 230 unidades: **la diferencia con XGBoost está muy por debajo del ruido y la de la regresión es del orden del ruido**.
- **Costo de limitar la capacidad:** si solo se puede llamar al 20 % mejor puntuado, el costo sube de 0,3326 a ≈ 0,403, unas **7.000 unidades por campaña**.
- **¿Cambia la elección si cambia R?** No. Con R de 2 a 12, LightGBM y XGBoost son siempre los dos mejores (XGBoost con R = 2 y 3; LightGBM con R = 5 o más) y la regresión queda a 0,003-0,004; el árbol pierde en todos los R. La regla simple deja de llamar (coincide con no llamar a nadie) con R ≤ 3.

## Finalistas

| Finalista | Por qué (consistencia, costo, tiempo, interpretabilidad) | Qué podría cambiar con la optimización |
|---|---|---|
| **LightGBM** | Menor costo (0,3326 ± 0,0023); gana en 5 de 5 pliegues a la regresión y al bosque; empata con XGBoost y se desempata por tiempo (≈ 2,5 s frente a ≈ 4,6 s); calibrado (0,010); PR-AUC 0,349 | Árboles, tasa de aprendizaje, hojas, regularización; **elegir el umbral** con la capacidad real; comprobar si XGBoost se acerca tras ajustar ambos |
| **Regresión logística (con edad como curva)** | Costo 0,3352, ≈ 260 unidades más que LightGBM (del orden del ruido); supera a bosque, árbol y líneas base en los 5 pliegues; calibrada; **la única que se explica con una fórmula** | Más curvas e interacciones (por ejemplo edad × antigüedad del vehículo); regularización |

**Modelos descartados y por qué:**
- **XGBoost:** empate práctico con LightGBM y casi el doble de lento; queda **como respaldo**.
- **Bosque aleatorio:** peor costo que la regresión en los 5 pliegues, 16 veces más lento que LightGBM y con probabilidades peor calibradas.
- **Árbol de decisión:** PR-AUC 0,31 frente a 0,34 de la regresión; sirve para **explicar** reglas, no para decidir.
- **Líneas base:** cumplieron su papel; ningún modelo real las pierde.

**Por qué el torneo no elige un campeón:** con parámetros de partida, la ventaja de LightGBM sobre XGBoost no pasa +1 y la de la regresión es del orden del ruido; la optimización puede mover el orden. Y ninguna cifra viene de la prueba cerrada: solo la etapa 7 dirá qué tan bueno es el modelo que se elija.

## Efectos que la métrica principal no ve

- **A quién deja de llamar** (LightGBM, predicciones fuera de muestra, umbral 16,7 %; **vista previa**, la auditoría completa es de la etapa 7):

| Grupo | Clientes | Tasa real | % llamados | Recall | Precisión |
|---|---|---|---|---|---|
| Mujeres | 140.107 | 10,4 % | 29,7 % | 84,5 % | 29,7 % |
| Hombres | 164.780 | 13,8 % | 41,8 % | 89,3 % | 29,5 % |
| 20-25 años | 91.667 | 3,5 % | **5,6 %** | **33,3 %** | 20,8 % |
| 26-35 | 57.712 | 11,4 % | 31,0 % | 92,5 % | 33,9 % |
| 36-45 | 56.414 | 21,5 % | 65,1 % | 97,8 % | 32,3 % |
| 46-55 | 49.250 | 19,8 % | 65,3 % | 97,7 % | 29,6 % |
| 56-65 | 27.375 | 14,0 % | 55,0 % | 90,8 % | 23,1 % |
| 66 o más | 22.469 | 8,4 % | **15,6 %** | **34,9 %** | 18,7 % |

- **Género:** el modelo **sí usa `Gender`** (decisión del grupo) y llama más a los hombres porque compran más; **la precisión es prácticamente idéntica (29,5 % y 29,7 %)**: una llamada rinde igual en ambos grupos. La brecha de recall es de 4,8 puntos. Como el género entra directamente al modelo, **Legal debe aprobar su uso** y hay que repetir esta tabla con la prueba cerrada.
- **Edad (el riesgo):** a los de 20-25 años y a los de 66 o más casi no se les llama (recall de 33 % y 35 %). Compran poco y llamarlos no compensa con R = 5, pero el costo agregado esconde que **una parte importante de sus compradores no recibe la oferta**: en el entrenamiento, **2.157 compradores de 20-25 años** (67 % de los suyos) y **1.225 de 66 o más** (65 %) no son llamados. Es una decisión de **política comercial**, no un fallo del modelo.
- **Operación:** todos reentrenan en menos de un minuto (el bosque, ≈ 41 s). El tiempo no decide, salvo para descartar al bosque.

## Decisiones del negocio antes de la etapa 6 (estado de cada una: `reports/decisiones_del_grupo.md`)

| # | Decisión | Propuesta |
|---|---|---|
| 1 | ¿Se exige explicar cada llamada? | Sí para el modelo que se despliegue frente a clientes o reguladores; entonces la regresión pasa a primera línea (cuesta ≈ 0,8 % del costo) |
| 2 | Capacidad real de llamadas | Confirmar con ventas: 20 %, 36 % (lo que contacta el umbral) u otra cifra; define si se opera por umbral o por capacidad fija |
| 3 | Valor de R | Estimar margen por venta ÷ costo de llamada. No cambia los finalistas, pero fija el umbral y el ahorro absoluto |
| 4 | Política para clientes de 20-25 y de 66 o más | Definir si hay un piso de contacto o una oferta distinta |
| 5 | Criterio de reemplazo del modelo | Reentrenar si la tasa real de aceptación se aleja de la predicha más de un 10 % relativo durante 2 campañas |
| 6 | Uso de `Gender` y del canal de venta | `Gender` se conserva (decisión del grupo, con aprobación de Legal); el canal se elimina por posible fuga hasta confirmar si se conoce al llamar |
