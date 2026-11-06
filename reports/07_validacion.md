# Validación e interpretación

> Resultado de `notebooks/07_validacion_interpretacion.ipynb`, ejecutado el 2026-11-05. Modelo **sin `Policy_Sales_Channel` y con `Gender`** (decisiones D12 y D13).
> Todo lo que está aquí se puede sostener ante una pregunta del instructor; las decisiones congeladas están en `reports/07_decisiones_congeladas.json` y las métricas en `reports/07_metricas_test.json`.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | **LightGBM** | Menor costo en el torneo (0,3326) y mejor que la regresión en clientes reservados (intervalo [+0,0002; +0,0055]); decisión D10, con la regresión como alternativa explicable |
| Parámetros (optimizados o de partida) | **De partida** (200 árboles, tasa 0,08, 31 hojas, 100 clientes mínimos por hoja, `subsample` 0,8, `colsample_bytree` 0,8, `reg_lambda` 0) | Etapa 6: la optimización no fue demostrablemente mejor (intervalo [-0,0021; +0,0018], cruza el cero) |
| Variables | Sin `Policy_Sales_Channel` (D13), sin `Vintage` ni `Driving_License`, **con `Gender`** (D12) | Etapa 4 y decisión del grupo del 2026-11-05 |
| ¿Calibrar las probabilidades? | **No** | Con el 25 % de clientes reservados del entrenamiento: calibrar no mejora el log loss (-0,00005) ni el costo (+0,0002), y la mayor diferencia predicha-real por decil empeora (0,008 → 0,016) |
| Métrica principal | Costo esperado por cliente (R = 5) | D01 |
| Regla de decisión | Llamar si P(compra) > 1/(R+1) = 0,1667 | D08 |
| **Fecha y hora en que se congelaron** | **2026-11-05 19:09** | Guardado en `reports/07_decisiones_congeladas.json` antes de cargar la prueba |

## 2. Calibración (con clientes reservados, no con la prueba)

- ¿Se evaluó? ☒ sí
- Resultado y decisión: LightGBM sin calibrar ya está bien calibrado (mayor diferencia entre probabilidad predicha y real en un decil: 0,008). La regresión isotónica no mejora log loss (0,2672 en ambos) ni Brier (0,0874) y hace peor la mayor diferencia por decil (0,016). **No se calibra.**

## 3. La prueba, abierta **una sola vez**

- Fecha y hora en que se abrió (la marca está en `reports/prueba_abierta.txt`): **2026-11-05 19:09**. 76.222 clientes; tasa de aceptación 12,26 %.
- ¿Se cambió algo del modelo después de verla? ☒ **no.** **Declaración:** la primera ejecución del notebook falló en la sección de SHAP por un error de escritura en el código (el nombre de una variable), **después** de haber abierto la prueba y calculado las métricas. Se corrigió ese error de código y se volvió a ejecutar todo el notebook. El modelo, sus parámetros y las decisiones no cambiaron (semillas fijas); las cifras de la segunda ejecución son las mismas. La marca de apertura conserva la hora de la primera ejecución.

| Métrica | Modelo final (LightGBM) | Baseline (llamar si hubo daño) | Alternativa (regresión) | Intervalo del 95 % (clientes) del modelo final |
|---|---|---|---|---|
| **Costo por cliente (principal)** | **0,3317** | 0,3967 | 0,3349 | [0,3264; 0,3369] |
| PR-AUC (control 1) | 0,3533 | 0,2357 | 0,3437 | no calculado |
| ROC-AUC (control 2) | 0,8519 | 0,7709 | 0,8485 | no calculado |
| Costo si solo se llama al 20 % mejor puntuado | 0,3988 | 0,5229 | 0,4040 | no calculado |
| Recall de compradores | 0,875 | 0,980 | 0,875 | — |
| Precisión (llamados que compran) | 0,296 | 0,238 | 0,294 | — |
| % de clientes contactados | 36,2 % | 50,5 % | 36,5 % | — |
| Log loss / Brier | 0,2672 / 0,0875 | 0,2924 / 0,0940 | 0,2690 / 0,0880 | — |

**¿Mejora al baseline con confianza?** **Sí.** Modelo menos baseline: **-0,0650 por cliente**, intervalo del 95 % **[-0,0700; -0,0607]**: todo el intervalo queda por debajo de cero. Son **≈ 6.500 unidades de llamada ahorradas por cada 100.000 clientes** (16,4 %). Coincide con la validación cruzada (0,3326), así que no hay señal de sobreajuste.
**Contra la regresión:** -0,0031, intervalo **[-0,0060; -0,0006]**: LightGBM es mejor con confianza del 95 %, por una diferencia pequeña (≈ 310 unidades por 100.000 clientes, menos del 1 %).

## 4. Errores y carga de trabajo

| Segmento | Casos | Tasa real | % que el modelo marca | Recall | Precisión | Compradores no llamados |
|---|---|---|---|---|---|---|
| Mujeres | 34.913 | 10,2 % | 29,6 % | 84,5 % | 29,2 % | 552 |
| Hombres | 41.309 | 14,0 % | 41,8 % | 89,3 % | 29,9 % | 616 |
| 20-25 años | 22.838 | 3,6 % | **5,7 %** | **33,3 %** | 20,6 % | 542 |
| 26-35 | 14.595 | 11,2 % | 31,0 % | 91,8 % | 33,2 % | 135 |
| 36-45 | 14.118 | 21,7 % | 65,5 % | 98,1 % | 32,5 % | 59 |
| 46-55 | 12.299 | 19,4 % | 64,9 % | 98,1 % | 29,4 % | 45 |
| 56-65 | 6.772 | 14,6 % | 56,1 % | 92,8 % | 24,1 % | 71 |
| 66 o más | 5.600 | 8,1 % | **13,6 %** | **30,4 %** | 18,1 % | 316 |

- **¿Hay un segmento al que le va peor?** Sí: **20-25 años y 66 o más** (recall de 33 % y 30 %). Compran poco (3,6 % y 8,1 %) y llamarlos no compensa con R = 5, pero 542 y 316 compradores reales de la prueba no reciben la oferta. Es una decisión de **política comercial**, no un fallo del modelo (**P04**). Confirma lo visto en validación cruzada.
- **Género:** el modelo **usa `Gender`** y llama más a los hombres (41,8 % frente a 29,6 %), pero compran más (14,0 % frente a 10,2 %) y la **precisión es parecida** (29,9 % y 29,2 %): una llamada rinde casi igual. La brecha de recall es de 4,8 puntos (89,3 % frente a 84,5 %). Al usar el género directamente, **Legal debe aprobar su uso**.
- **Carga de trabajo:** el modelo marca al **36,2 %** de los clientes y en realidad compra el 12,3 %: **≈ 3 llamadas por cada comprador real**. Es el costo de querer encontrar al 87,5 % de los compradores con R = 5.

## 5. Interpretación

- **Variables que más pesan** (SHAP, impacto medio absoluto, escala logit): `Previously_Insured` 2,32; `Vehicle_Damage` 1,03; `Region_Code` 0,35; `Age` 0,33; `Vehicle_Age` 0,13; `Gender` 0,09; `Annual_Premium` 0,09; `Premium_is_minimum` 0,02. **Para el negocio:** la decisión depende sobre todo de dos preguntas: si el cliente ya tiene seguro de vehículo (casi nunca compra) y si el vehículo tuvo un daño (compra mucho más). Región y edad afinan el orden dentro de esos grupos. El género aporta poco.
- **Dos clientes concretos:** a un hombre de 31 años sin seguro previo y con daño (P = 52 %) se le llama sobre todo por `Previously_Insured` (+1,96) y `Vehicle_Damage` (+1,13); a una mujer de 79 años con seguro previo y sin daño (P ≈ 0 %) no se le llama por `Previously_Insured` (-2,62), la edad (-0,92) y la ausencia de daño (-0,88).
- **Límite de la explicación:** SHAP explica al modelo, no al mundo; no dice si el modelo acertó, y las variables correlacionadas (`Previously_Insured` y `Vehicle_Damage`, `Age` y `Vehicle_Age`) se reparten el crédito. Que el daño "cause" la compra es una hipótesis del negocio, no algo que los datos prueben (**P09**).
- **Atributos sensibles o de uso regulado:** `Gender` (usado directamente por decisión del grupo) y `Age` (la edad cambia mucho el trato: casi no se llama a los de 20-25 y 66+). **Qué se hace:** auditoría por género y edad (sección 4), aprobación de Legal sobre el género y definición de un piso de contacto por edad.

## 6. Conclusión

- **¿El modelo sirve para la decisión del caso?** Sí, con condiciones: reduce el costo de contacto un **16,4 %** frente a la mejor regla sin modelo (intervalo claramente fuera del cero) y la cifra de la prueba coincide con la validación. **Condiciones:** (1) Legal aprueba el uso de `Gender`; (2) el grupo define la política para los de 20-25 y 66 o más; (3) se confirma R (**P01**) y que el canal de venta se conoce o no al llamar (**P11**; sin él el modelo cuesta ≈ 800 unidades más por 100.000 clientes).
- **Qué NO debe hacerse con él:** no usarlo para negar un seguro ni para excluir por edad o género (solo ordena a quién llamar primero); no aplicarlo a otra aseguradora, otro país o otra época sin revalidar; no reportar el costo como dinero sin confirmar R; no volver a abrir la prueba para ajustar el modelo.
- **Lo que no se evaluó:** estabilidad en el tiempo, deriva de los datos, comportamiento en otras regiones o aseguradoras y el efecto real de una campaña (el dataset es histórico, no experimental).
