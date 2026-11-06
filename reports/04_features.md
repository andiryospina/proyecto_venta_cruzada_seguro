# Informe de variables

> **BORRADOR para revisión del grupo.** Resultado de `notebooks/04_features.ipynb`, reejecutado el 2026-11-05 **sin `Policy_Sales_Channel` y con `Gender`**. Cada idea de variable es una **hipótesis medida** con la misma validación;
> se conserva solo si la mejora supera el ruido entre pliegues. Tabla completa y reproducible: `reports/04_features_tabla.csv`.
> Estados de decisión: **[DECIDIDO]** (resuelto con evidencia del proyecto), **[ADOPTADO]** (propuesta vigente por defecto hasta que el grupo diga lo contrario) o **[PENDIENTE: dato externo]** (no se puede resolver con estos datos); registro en `reports/decisiones_del_grupo.md`.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 1.

## Resumen para quien decide

- **Dos decisiones del grupo cambian esta versión:** (1) `Policy_Sales_Channel` se **elimina** en la limpieza por posible fuga de información (decisión 8 del EDA); (2) `Gender` se **conserva** en el modelo (2026-11-05).
- Con las variables que tenemos, un modelo de árboles cuesta **0,332 unidades por cliente** frente a **0,398** de la regla simple "llamar si hubo daño": **≈ 16 % menos**. Con el canal de venta el costo era 0,3245: quitarlo cuesta ≈ 0,008 por cliente (≈ 800 unidades por 100.000 clientes).
- **Ninguna de las 5 ideas para agregar variables mejora al modelo de árboles.** Inventar variables nuevas no era el camino.
- Para la **regresión logística**, tratar la edad como curva sube la PR-AUC de 0,318 a 0,339 (**6,8 veces el ruido**, gana en los 5 pliegues).
- Quitar `Vintage` y `Driving_License` **no tiene costo medible**. Quitar además `Gender` tampoco (costo 0,3327 frente a 0,3322), pero el grupo decidió **conservarla**.
- Quitar la prima **sí** empeora al modelo de árboles (1,5 veces el ruido): se queda.

## Cómo se midió

- **Modelos (parámetros fijos):** LightGBM (200 árboles, tasa 0,08, 31 hojas) y regresión logística (C = 1, con variables escaladas). Se usan dos para separar lo que las variables aportan de lo que el modelo ya descubre solo.
- **Métrica principal (y por qué):** **PR-AUC**, porque solo el 12,26 % de los clientes acepta y mide qué tan arriba quedan los compradores en la lista.
- **Métricas de control:** **costo por cliente** con R = 5 (umbral 16,7 %), log loss y ROC-AUC.
- **Pliegues:** 5 estratificados por `Response`, semilla 42, **los mismos de la etapa 3**, solo sobre el entrenamiento (304.887 clientes). Un cliente por fila, así que no hace falta partir por grupo. La prueba cerrada **no se abrió**.
- **Regla de decisión escrita antes de medir [ADOPTADO · D04]:**
  - **R1 Evidencia:** agregar una variable solo si mejora / ruido > 1 en PR-AUC y gana en 4 de 5 pliegues.
  - **R2 Disponibilidad:** debe conocerse al momento de llamar.
  - **R3 Complejidad:** no agregar datos que el equipo comercial no pueda dar o mantener, salvo evidencia muy clara (mejora / ruido > 3).
  - **R4 Retiro:** retirar una variable si quitarla empeora menos de 1 ruido.
  - **R5 Equidad:** retirar variables sensibles si no cuestan nada; nunca agregarlas para ganar precisión. **Excepción vigente:** el grupo conserva `Gender` (2026-11-05).

## Tabla de ideas medidas

> La fila 0 es la **referencia** (variables limpias de la etapa 3, con regiones raras agrupadas; sin canal de venta). "Mejora / ruido" = mejora de la PR-AUC dividida entre su desviación entre pliegues; menor que ~1 está dentro del ruido.

| # | Idea (variable y cómo se calcula) | ¿Se conoce al predecir? | PR-AUC LightGBM (± ruido) | Mejora / ruido LightGBM | Mejora / ruido regresión | Decisión |
|---|---|---|---|---|---|---|
| 0 | **Referencia** | — | 0,3498 (± 0,0032) | 0 | 0 (PR-AUC 0,3177) | — |
| 1 | Recorte de la prima en el percentil 99 del entrenamiento | ☒ sí | 0,3489 (± 0,0024) | -0,40 | -0,01 | ☒ descartar |
| 2 | Segmento comercial: 1 si no tiene seguro y sí tuvo daño | ☒ sí | 0,3490 (± 0,0039) | -0,22 | -0,01 | ☒ descartar |
| 3 | Edad como curva suave (*splines*) | ☒ sí | 0,3491 (± 0,0024) | -0,33 | **+6,78** | ☒ conservar **solo para la regresión** |
| 4 | Tasa histórica de región | ☒ sí, con tabla a mantener | 0,3492 (± 0,0028) | -0,24 | **-2,20** | ☒ descartar |
| 5 | Prima relativa a la mediana de su región | ☒ sí, con medianas a mantener | 0,3489 (± 0,0040) | -0,23 | 0,00 | ☒ descartar |
| 6 | Sin `Vintage` ni `Driving_License` | — | 0,3492 (± 0,0033) | -0,20 | -0,05 | ☒ **retirar** |
| 7 | Sin `Gender` | — | 0,3485 (± 0,0030) | -0,43 | -0,13 | ☒ **se conserva `Gender`** por decisión del grupo |
| 8 | No agrupar regiones raras | ☒ sí | 0,3498 (± 0,0032) | 0,00 | 0,00 | ☒ mantener el agrupamiento (hoy no hay regiones raras) |
| 9 | Sin prima ni su marca | — | 0,3443 (± 0,0036) | **-1,53** | -0,15 | ☒ **conservar la prima** |

**Combinaciones finales (confirmación):**

| Variante | PR-AUC | Mejora / ruido | Costo por cliente | Datos que pide la app |
|---|---|---|---|---|
| LightGBM referencia | 0,3498 | 0 | 0,3322 | 9 |
| LightGBM A (sin `Vintage`, licencia ni `Gender`) | 0,3489 | -0,30 | 0,3326 | 6 |
| LightGBM B (A y sin prima) | 0,3448 | -1,66 | 0,3335 | 5 |
| **LightGBM 6 (sin `Vintage` ni licencia, con `Gender`)** | 0,3492 | -0,20 | **0,3326** | **7** |
| Regresión referencia | 0,3177 | 0 | 0,3540 | 9 |
| Regresión C (A + edad como curva) | 0,3394 | +7,68 | 0,3359 | 6 |
| Regresión D (B + edad como curva) | 0,3377 | +7,51 | 0,3357 | 5 |
| **Regresión E (6 + edad como curva, con `Gender`)** | **0,3392** | **+7,22** | **0,3352** | **7** |

## Decisiones y motivos

- **Idea 1, recorte de la prima: descartar.** -0,40 en árboles y -0,01 en regresión. Los árboles ya son robustos a los extremos; la regresión no mejora.
- **Idea 2, segmento comercial: descartar como variable.** -0,22 y -0,01. Los modelos ya aprenden esa interacción (97,7 % de los compradores). Se conserva como **regla de contacto** de negocio.
- **Idea 3, edad como curva: conservar solo para la regresión.** +6,78 en regresión (gana en 5 de 5 pliegues; el costo baja de 0,3540 a 0,3352 y mejora el log loss). Para árboles -0,33: ya parten la edad donde conviene.
- **Idea 4, tasa histórica de región: descartar.** Empeora la regresión (-2,20), es la que más empeora el costo en árboles (0,3342 frente a 0,3322) y obliga a mantener una tabla externa (R3).
- **Idea 5, prima relativa a la región: descartar.** Dentro del ruido y exige mantener medianas por región.
- **Idea 6, sin `Vintage` ni `Driving_License`: retirar.** Sin costo medible (R4); dos preguntas menos en la app.
- **Idea 7, sin `Gender`: se conserva por decisión del grupo.** -0,43 en árboles (dentro del ruido) y -0,13 en regresión: la evidencia dice que da igual, de modo que cumpliría R4 y R5, pero el grupo la mantiene. **Exige auditoría de equidad por género y edad en la etapa 7 y aprobación de Legal.**
- **Idea 8, agrupar regiones raras: mantener.** Idéntica a la referencia porque ninguna región tiene menos de 100 clientes; la regla queda como protección ante regiones nuevas.
- **Idea 9, quitar la prima: conservarla.** -1,53 en árboles y 0 de 5 pliegues ganados: empeora de verdad. Contradice la lectura del EDA (la prima aportaba poco por sí sola): los árboles la usan combinada con otras variables.
- **Las ideas descartadas** (1, 2, 4 y 5) quedan registradas con su cifra para no volver a probarlas sin una razón nueva.

## Comprobaciones de que no hay fuga

- **Cada pliegue aprende lo suyo:** el percentil 99 de la prima aprendido por pliegue varía (73.021 a 73.221), distinto del de todo el entrenamiento (73.132).
- **Etiquetas barajadas:** con las respuestas mezcladas al azar, la PR-AUC queda en 0,1223 (referencia) y 0,1231 (con tasa histórica de región), igual a la proporción de compradores (0,1226). No hay fuga.
- **`id` pesa exactamente 0** en la importancia por permutación: el pipeline la ignora.
- **Importancia por permutación (LightGBM, pliegue 1):** `Previously_Insured` 0,099; `Age` 0,092; `Vehicle_Damage` 0,065; `Vehicle_Age` 0,038; `Region_Code` 0,025; `Annual_Premium` 0,009; el resto (`Premium_is_minimum`, `Vintage`, `Gender`, `Driving_License`) pesa 0,002 o menos.

## Valor para el negocio

Costo promedio por cliente (R = 5), medido en los mismos pliegues de validación:

| Estrategia | Costo por cliente | Ahorro frente a la regla simple por 100.000 clientes |
|---|---|---|
| Llamar a todos | 0,877 | -47.940 unidades de llamada |
| No llamar a nadie | 0,613 | -21.478 |
| Regla simple: llamar si hubo daño | 0,398 | 0 |
| Regresión + edad como curva (E, con `Gender`) | 0,3352 | +6.285 (15,8 %) |
| LightGBM (variante 6, con `Gender`) | 0,3326 | **+6.543 (16,4 %)** |

Un ruido de costo equivale a ≈ 266 unidades de llamada por 100.000 clientes; la diferencia entre regresión y árboles (≈ 260) es comparable al ruido. Si el negocio valora la **explicabilidad**, la regresión es una opción seria; los árboles ganan en PR-AUC (0,349 frente a 0,339, unas 3 veces el ruido).

## Segunda ronda: variables nuevas conservando todas las actuales

Se mantuvieron las variables actuales y se crearon 6 derivadas (código en `src/proyecto/features/engineering.py`, con pruebas). Misma validación y misma regla. Referencias: LightGBM con las variables limpias (PR-AUC 0,3498) y regresión con edad como curva (0,3392). Tabla completa: `reports/04_features_tabla_nuevas.csv`.

| # | Variable nueva | Qué pregunta de negocio responde | Columnas | Mejora / ruido LightGBM | Mejora / ruido regresión | Decisión |
|---|---|---|---|---|---|---|
| N1 | Tamaño de la región | ¿Región grande o de nicho? | +1 | -0,02 | +0,01 | ☒ descartar |
| N2 | Puntaje de necesidad (0 a 4) | ¿Qué tan necesitado de seguro está? | +1 | -0,23 | 0,00 | ☒ descartar |
| N3 | Perfil de 12 combinaciones | ¿En qué perfil cae? | +12 | -0,41 | +0,03 | ☒ descartar |
| N4 | Joven con vehículo nuevo | ¿Cruce de dos grupos que casi no compran? | +1 | -0,11 | +0,23 (5 de 5 pliegues) | ☒ descartar |
| N5 | Prima frente a su tramo de edad | ¿Paga más o menos que sus pares? | +1 | -0,27 | +0,04 | ☒ descartar |
| N6 | Fracción de vida como cliente | ¿Cliente antiguo para su edad? | +1 | -0,53 | -0,05 | ☒ descartar |
| — | **Las seis juntas** | — | +17 | **-0,71** (PR-AUC 0,3470) | +0,12 (0,3396; 5 de 5 pliegues) | ☒ descartar |

- **Ninguna cumple la regla R1** (mejora / ruido > 1 y 4 de 5 pliegues). En LightGBM todas quedan por debajo de la referencia y el costo no cambia (entre 0,3318 y 0,3327 frente a 0,3322).
- **En la regresión la mejor es N4** (PR-AUC de 0,3392 a 0,3399), pero el costo **no cambia** (0,3352) y la mejora es 0,23 veces el ruido.
- **Por qué no aportan, aunque en el EDA (sección 4.2) muestren señal clara:** N2 y N3 son funciones exactas de tres columnas que el modelo ya tiene; N4 reexpresa edad y antigüedad del vehículo (correlación 0,82 entre sí); N6 es en esencia `1 / edad`; N1 solo cuenta clientes por región, que el modelo ya conoce; N5 es más débil que la prima original.
- **Conclusión:** una señal descriptiva clara **no es valor incremental**. El techo del modelo está en los **datos**, no en el modelado.
- **Datos nuevos que valdría la pena evaluar (hipótesis, no medibles con este dataset) [PENDIENTE: dato externo · P08]:** 1) historial de contactos; 2) fecha de vencimiento del seguro de vehículo actual; 3) tiempo desde el último siniestro y su monto; 4) número de vehículos y pólizas del hogar; 5) canal y horario preferidos de contacto; 6) ingreso (solo con revisión legal por el riesgo de equidad). Cada uno se mediría con este mismo experimento.

## Supuestos y riesgos

| # | Supuesto o riesgo | Mitigación propuesta | Responsable |
|---|---|---|---|
| 1 | **R = 5** es una hipótesis; fija el umbral de contacto en 16,7 %. Cambia el costo absoluto, no el orden entre variantes **[PENDIENTE: dato externo · P01]** | Confirmar con la aseguradora el margen de una venta y el costo de una llamada | Negocio |
| 2 | La app debe poder pedir y validar 7 datos: `Previously_Insured`, `Vehicle_Damage`, `Vehicle_Age`, `Age`, `Gender`, región y prima | Validar con ventas que el vendedor los conoce **antes** de llamar (R2) | Negocio |
| 3 | `Gender` se conserva como variable del modelo (decisión del grupo): riesgo de trato distinto por género | Medir recall y tasa de contacto por género y tramo de edad en la validación (etapa 7); Legal aprueba su uso | Datos y Legal |
| 4 | `Policy_Sales_Channel` se eliminó por posible fuga; su ausencia cuesta ≈ 0,008 por cliente **[PENDIENTE: dato externo · P11]** | Confirmar si el canal se conoce antes de decidir a quién llamar; si sí, medirlo de nuevo con y sin | Negocio y Datos |
| 5 | El 17 % de las primas vale exactamente 2.630 (parece un mínimo impuesto) | Vigilar la distribución de la prima en producción | Datos |
| 6 | Todo sale de un solo dataset histórico | Comparar periódicamente la tasa real de aceptación con la predicha | Datos y Negocio |
| 7 | Todas las cifras son de validación cruzada; la prueba cerrada no se ha abierto | Abrirla **una sola vez** en la etapa 7 | Datos |

## Qué se lleva el pipeline final

- **Datos de entrada que pide la app (7):** `Previously_Insured`, `Vehicle_Damage`, `Vehicle_Age`, `Age`, `Gender`, `Region_Code`, `Annual_Premium` (más `Premium_is_minimum`, que se calcula sola).
- **Se retiran:** `Policy_Sales_Channel` (se elimina en la limpieza), `Vintage`, `Driving_License` e `id`.
- **Transformaciones dentro del `Pipeline`:** regiones con menos de 100 clientes (y las desconocidas) → "otros"; para la regresión, edad como curva y variables escaladas; para LightGBM, ninguna adicional.
- **Código:** `src/proyecto/features/engineering.py`, `src/proyecto/models/train.py` y `src/proyecto/models/metrics.py`, con pruebas en `tests/`.
