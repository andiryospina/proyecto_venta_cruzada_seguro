# Informe del torneo de modelos

> **BORRADOR para revisión del grupo.** Resultado de `notebooks/05_torneo.ipynb`. El torneo **descarta**: elige 1-2 finalistas con evidencia, no un campeón definitivo.
> Todas las cifras son de **validación cruzada** sobre el entrenamiento; la prueba cerrada **no se abrió**. Tabla reproducible: `reports/05_torneo_tabla.csv`.
> Lo marcado **[DECIDE EL GRUPO]** necesita una decisión de negocio. Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2.

## Resumen para quien decide

- **LightGBM** tiene el menor costo: **0,3245** por cliente, frente a **0,398** de la regla "llamar si hubo daño" y **0,613** de no llamar a nadie. Ahorra **≈ 7.400 unidades de llamada por cada 100.000 clientes** (18,5 %) frente a la regla simple.
- **LightGBM y XGBoost empatan en la práctica** (diferencia 0,0014; +0,99 veces el ruido). Se elige LightGBM por ser casi el doble de rápido.
- **La regresión logística**, el modelo explicable, cuesta **0,3278**: ≈ 340 unidades más por 100.000 clientes que LightGBM (≈ 1 % del costo), y **supera al bosque, al árbol y a las líneas base**.
- **Finalistas: LightGBM y regresión logística.**
- **Cuidado de equidad por edad:** con el umbral de decisión, el modelo casi no llama a los de 20-25 años ni a los de 66 o más (recall de 36 % y 40 %).

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos:** 5 pliegues estratificados por `Response`, semilla 42, **los mismos de las etapas 3 y 4**. Un cliente por fila (`id` único), así que no hace falta partir por grupo. 304.887 clientes de entrenamiento.
- **Líneas base:** (1) **no llamar a nadie** (predice la proporción de compradores, 12,26 %): costo 0,613; (2) **la regla de negocio "llamar si hubo daño"** (aprende la tasa con y sin daño): costo 0,398. Ningún modelo real las pierde.
- **Métrica principal (la de negocio):** **costo promedio por cliente** con R = 5 (umbral 16,7 %), en unidades de llamada. Complemento que no depende de calibración: **costo si solo se llama al 20 % mejor puntuado**. **R = 5 es una hipótesis [DECIDE EL GRUPO].**
- **Métricas técnicas:** ROC-AUC, PR-AUC, exactitud balanceada, precisión y recall por clase, F1 macro, log loss, Brier, recall y *lift* en el 20 % mejor puntuado.
- **Variables usadas** (decididas en `reports/04_features.md`): sin `Vintage`, `Driving_License` ni `Gender`, con canales y regiones raros agrupados. La regresión recibe además **la edad como curva** (+6,2 veces el ruido en la etapa 4); los árboles no la necesitan.
- **Criterios de elección, en orden [DECIDE EL GRUPO: confirmar]:** consistencia (gana en 4 de 5 pliegues y supera 1 vez el ruido) → costo → ranking sin depender del umbral → tiempo y simplicidad → explicabilidad (solo si la exige el negocio o el regulador).

## Tabla comparativa

> Media ± desviación entre pliegues. Ordenada por costo (menor es mejor).

| Modelo | Costo por cliente (± ruido) | Costo si solo se llama al 20 % | Unidades por 100.000 clientes | Segundos de ajuste |
|---|---|---|---|---|
| **LightGBM** | **0,3245** (± 0,0036) | 0,3849 | **32.446** | 2,8 |
| XGBoost | 0,3259 (± 0,0038) | 0,3845 | 32.586 | 5,2 |
| **Regresión logística** | 0,3278 (± 0,0027) | 0,3906 | 32.782 | 2,1 |
| Bosque aleatorio | 0,3355 (± 0,0033) | 0,3903 | 33.548 | 25,3 |
| Árbol de decisión | 0,3377 (± 0,0014) | 0,4304 | 33.767 | 0,8 |
| Línea base: llamar si hubo daño | 0,3980 (± 0,0023) | 0,5275 | 39.803 | — |
| Línea base: no llamar a nadie | 0,6128 | 0,6653 | 61.282 | — |

## Métricas técnicas

> Media entre pliegues. Las de ranking usan las probabilidades; las de decisión usan el umbral de 16,7 %. Clase de interés = compradores.

| Modelo | ROC-AUC | PR-AUC | Exactitud balanceada | Precisión (compradores) | Recall no compradores | Recall compradores | F1 macro | Log loss | Brier | Recall en el 20 % mejor |
|---|---|---|---|---|---|---|---|---|---|---|
| LightGBM | 0,858 | **0,371** | 0,796 | 0,303 | 0,721 | 0,871 | **0,639** | **0,265** | **0,087** | 58,2 % |
| XGBoost | **0,858** | 0,370 | 0,795 | 0,303 | 0,721 | 0,869 | 0,639 | 0,265 | 0,087 | 58,2 % |
| Regresión logística | 0,854 | 0,356 | 0,794 | 0,301 | 0,718 | 0,869 | 0,637 | 0,267 | 0,087 | 57,4 % |
| Bosque aleatorio | 0,854 | 0,362 | 0,794 | 0,286 | 0,685 | **0,904** | 0,620 | 0,272 | 0,088 | 57,5 % |
| Árbol de decisión | 0,838 | 0,310 | 0,787 | 0,295 | 0,712 | 0,862 | 0,631 | 0,271 | 0,089 | 52,0 % |
| Línea base: llamar si hubo daño | 0,770 | 0,235 | 0,770 | 0,238 | 0,561 | 0,979 | 0,550 | 0,293 | 0,094 | 38,8 % |
| Línea base: no llamar a nadie | 0,500 | 0,123 | 0,500 | 0,000 | 1,000 | 0,000 | 0,467 | 0,372 | 0,108 | 20,1 % |

## ¿Coinciden los rankings de negocio y técnico?

> Posición entre los **5 modelos** (1 = mejor).

| Modelo | Costo (negocio) | ROC-AUC | F1 macro | Recall de compradores |
|---|---|---|---|---|
| LightGBM | 1 | 2 | 1 | 2 |
| XGBoost | 2 | 1 | 2 | 4 |
| Regresión logística | 3 | 4 | 3 | 3 |
| Bosque aleatorio | 4 | 3 | 5 | 1 |
| Árbol de decisión | 5 | 5 | 4 | 5 |

- **¿El mejor por costo también es el mejor por AUC?** Casi: LightGBM y XGBoost son 1.º y 2.º en costo, ROC-AUC, PR-AUC y F1; el orden entre ellos varía en milésimas. El resultado **no depende de la librería**.
- **¿Hay modelos con AUC casi igual pero costo distinto?** **Sí: bosque aleatorio y regresión logística** (ROC-AUC 0,854 los dos; costo 0,3355 frente a 0,3278). **Deciden distinto:** el bosque contacta más clientes (38,8 % frente a 35,4 %), con más recall (90,4 % frente a 86,9 %) y menos precisión (28,6 % frente a 30,1 %), porque sus **probabilidades no están calibradas**: en el grupo de mayor probabilidad dice 32,5 % y en realidad compra el 38,8 %. La regla de llamar con probabilidad > 16,7 % solo es óptima si la probabilidad es fiel.
- **¿Hay alguna clase con recall casi nulo?** Solo la línea base "no llamar a nadie" (recall 0 de compradores, por construcción). Entre los modelos reales, el recall de los no compradores va de 68 % a 72 %: ninguno sacrifica una clase. La regla "llamar si hubo daño" llama al 50,5 % y su recall de no compradores es de solo 56 %: gasta llamadas.

**Calibración** (diferencia máxima entre probabilidad predicha y real en un decil): XGBoost 0,0007 · regresión 0,004 · LightGBM 0,008 · **bosque 0,063**.

## Comparación pareada de los mejores

> Los 5 pliegues son los mismos para todos. "Diferencia / ruido" = diferencia media ÷ desviación de la diferencia pliegue a pliegue.

| Mejor | Contra | Métrica | Diferencia media | Pliegues que gana | Diferencia / ruido | Lectura |
|---|---|---|---|---|---|---|
| LightGBM | XGBoost | costo | +0,0014 | 4 de 5 | +0,99 | **Empate práctico** |
| LightGBM | XGBoost | PR-AUC | +0,0007 | 3 de 5 | +0,71 | Empate práctico |
| LightGBM | Regresión | costo | +0,0034 | **5 de 5** | +1,87 | Ventaja consistente, pequeña |
| LightGBM | Regresión | PR-AUC | +0,0143 | **5 de 5** | **+10,1** | Ventaja clara en ranking |
| LightGBM | Bosque | costo | +0,0110 | **5 de 5** | +3,29 | Ventaja clara |
| Regresión | Bosque | costo | +0,0077 | **5 de 5** | +4,51 | Un modelo simple le gana a 150 árboles |
| Regresión | Árbol | costo | +0,0099 | **5 de 5** | +3,26 | Ventaja clara |

## ¿Cuánto vale la diferencia?

- **Decisiones estimadas por campaña:** 100.000 clientes (supuesto de referencia **[DECIDE EL GRUPO]**).
- **Ahorro frente a la línea base "llamar si hubo daño":** LightGBM **+7.357** unidades de llamada (18,5 %); regresión +7.021 (17,6 %).
- **Ahorro frente a "no llamar a nadie":** LightGBM +28.836.
- **Diferencia entre el mejor y el siguiente:** LightGBM frente a XGBoost, 140 unidades; frente a la regresión, ≈ 340 unidades (≈ 1 % del costo total). El ruido del costo es ≈ 360 unidades: **ninguna de las dos diferencias es mayor que el ruido**.
- **Costo de limitar la capacidad:** si solo se puede llamar al 20 % mejor puntuado, el costo sube de 0,3245 a ≈ 0,385, unas **6.000 unidades por campaña**.
- **¿Cambia la elección si cambia R?** No. Con R de 2 a 12, LightGBM y XGBoost son siempre los dos mejores y la regresión queda a 0,003-0,005; el árbol pierde en todos los R. La regla simple deja de llamar (coincide con no llamar a nadie) con R ≤ 3.

## Finalistas

| Finalista | Por qué (consistencia, costo, tiempo, interpretabilidad) | Qué podría cambiar con la optimización |
|---|---|---|
| **LightGBM** | Menor costo (0,3245 ± 0,0036); gana en 5 de 5 pliegues a la regresión y al bosque; empata con XGBoost y se desempata por tiempo (≈ 3 s frente a ≈ 5 s); calibrado (0,008); PR-AUC 0,371 | Árboles, tasa de aprendizaje, hojas, regularización; **elegir el umbral** con la capacidad real; comprobar si XGBoost se acerca tras ajustar ambos |
| **Regresión logística (con edad como curva)** | Costo 0,3278, ≈ 340 unidades más que LightGBM (del orden del ruido); supera a bosque, árbol y líneas base en los 5 pliegues; calibrada; **la única que se explica con una fórmula** | Más curvas e interacciones (por ejemplo edad × antigüedad del vehículo, o el perfil de 12 combinaciones que quedó en observación en la etapa 4); regularización |

**Modelos descartados y por qué:**
- **XGBoost:** empate práctico con LightGBM y casi el doble de lento; queda **como respaldo**.
- **Bosque aleatorio:** peor costo que la regresión en los 5 pliegues, 9 veces más lento y con probabilidades mal calibradas.
- **Árbol de decisión:** PR-AUC 0,31 frente a 0,36 de la regresión; sirve para **explicar** reglas, no para decidir.
- **Líneas base:** cumplieron su papel; ningún modelo real las pierde.

**Por qué el torneo no elige un campeón:** con parámetros de partida, la ventaja de LightGBM sobre XGBoost no pasa +1 y la de la regresión es del orden del ruido; la optimización puede mover el orden. Y ninguna cifra viene de la prueba cerrada: solo la etapa 7 dirá qué tan bueno es el modelo que se elija.

## Efectos que la métrica principal no ve

- **A quién deja de llamar** (LightGBM, predicciones fuera de muestra, umbral 16,7 %; **vista previa**, la auditoría completa es de la etapa 7):

| Grupo | Clientes | Tasa real | % llamados | Recall | Precisión |
|---|---|---|---|---|---|
| Mujeres | 140.107 | 10,4 % | 29,4 % | 85,3 % | 30,3 % |
| Hombres | 164.780 | 13,8 % | 40,2 % | 88,2 % | 30,3 % |
| 20-25 años | 91.667 | 3,5 % | **5,8 %** | **36,3 %** | 22,0 % |
| 26-35 | 57.712 | 11,4 % | 29,0 % | 90,9 % | 35,6 % |
| 36-45 | 56.414 | 21,5 % | 63,9 % | 97,3 % | 32,7 % |
| 46-55 | 49.250 | 19,8 % | 63,7 % | 97,2 % | 30,2 % |
| 56-65 | 27.375 | 14,0 % | 51,3 % | 88,0 % | 24,0 % |
| 66 o más | 22.469 | 8,4 % | **16,7 %** | **40,2 %** | 20,2 % |

- **Género:** el modelo no usa `Gender`, pero llama más a los hombres porque compran más; **la precisión es idéntica (30,3 %)**: una llamada rinde igual en ambos grupos. La brecha de recall es de 2,9 puntos.
- **Edad (el riesgo):** a los de 20-25 años y a los de 66 o más casi no se les llama (recall de 36 % y 40 %). Compran poco y llamarlos no compensa con R = 5, pero el costo agregado esconde que **una parte importante de sus compradores no recibe la oferta**: en el entrenamiento, **2.061 compradores de 20-25 años** (64 % de los suyos) y **1.124 de 66 o más** (60 %) no son llamados. Es una decisión de **política comercial**, no un fallo del modelo.
- **Operación:** todos reentrenan en menos de un minuto (el bosque, ≈ 26 s). El tiempo no decide, salvo para descartar al bosque.

## Decisiones que necesitamos del negocio antes de la etapa 6 [DECIDE EL GRUPO]

| # | Decisión | Propuesta |
|---|---|---|
| 1 | ¿Se exige explicar cada llamada? | Sí para el modelo que se despliegue frente a clientes o reguladores; entonces la regresión pasa a primera línea (cuesta ≈ 1 % del costo) |
| 2 | Capacidad real de llamadas | Confirmar con ventas: 20 %, 35 % (lo que contacta el umbral) u otra cifra; define si se opera por umbral o por capacidad fija |
| 3 | Valor de R | Estimar margen por venta ÷ costo de llamada. No cambia los finalistas, pero fija el umbral y el ahorro absoluto |
| 4 | Política para clientes de 20-25 y de 66 o más | Definir si hay un piso de contacto o una oferta distinta |
| 5 | Criterio de reemplazo del modelo | Reentrenar si la tasa real de aceptación se aleja de la predicha más de un 10 % relativo durante 2 campañas |
