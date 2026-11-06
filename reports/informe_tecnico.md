# Informe técnico — Venta cruzada de seguro de vehículo

> **BORRADOR para revisión del grupo (2026-11-05).** Ensamblado a partir de los informes de `reports/`; las cifras coinciden con `reports/07_validacion.md`. Se entrega el domingo 15 de noviembre (hito H4).
> **Regla del informe:** cada decisión va con su motivo. Lo que depende de un dato externo está marcado **[PENDIENTE: dato externo]** y no se da por resuelto.

**Grupo:** **[PENDIENTE: P07]** (integrantes y roles) · **Repositorio:** `rigonzalezre-dot/proyecto_venta_cruzada_seguro` (rama `feature/eda-preprocesamiento`) · **App:** **[PENDIENTE]** (se despliega en la clase 5)

## Resumen ejecutivo

Una aseguradora quiere ofrecer un seguro de vehículo a clientes que ya tienen seguro de salud, y el equipo comercial debe decidir a quién llamar primero. Solo el 12,3 % de los clientes acepta. Construimos un modelo (LightGBM) que ordena a los clientes por probabilidad de compra y recomienda llamar a quien supere el 16,7 %, es decir, al 36 % de la lista.

En una prueba con 76.222 clientes que el modelo nunca vio y que se abrió **una sola vez**, el costo por cliente fue **0,3317** (intervalo del 95 %: 0,3264 a 0,3369) frente a **0,3967** de la mejor regla sin modelo ("llamar a quien tuvo un daño"). Son **≈ 6.500 unidades de llamada ahorradas por cada 100.000 clientes (16,4 %)**, con el intervalo de la diferencia entero por debajo de cero. La cifra supone que perder a un comprador cuesta 5 veces una llamada inútil (R = 5), una hipótesis **[PENDIENTE: P01]**.

Principales límites: el modelo usa la **edad y el género** (Legal debe aprobar el género) y casi no llama a menores de 26 ni a mayores de 65, aunque entre ellos hay compradores; y se **eliminó el canal de venta** por posible fuga, lo que cuesta ≈ 800 unidades por 100.000 clientes. Enlace de la app: **[PENDIENTE]**.

## 1. Caso de negocio

> Fuente: `reports/00_caso.md` (ficha en estado `borrador`; la aprueba el instructor, **P10**).

- **Quién decide y qué decide:** el equipo comercial decide a qué clientes llamar primero (hipótesis por confirmar, **P06**).
- **Con qué información:** edad, género, región, antigüedad del vehículo, daño previo, si ya tiene seguro de vehículo y prima anual.
- **Qué cuesta equivocarse:** no llamar a quien habría comprado es una venta perdida; llamar a quien no comprará es un costo de contacto. Se asume R = 5 (la venta perdida pesa 5 veces la llamada inútil) **[PENDIENTE: P01]**; los finalistas y el umbral no cambian con R entre 2 y 12.
- **Cómo se midió el éxito:** costo esperado por cliente (negocio) y PR-AUC (técnica), frente a la regla simple "llamar si hubo daño" (D01, D03).

## 2. Datos y limpieza

> Fuente: `reports/01_eda.md`, `especificaciones/03-preprocesamiento.md` y `src/proyecto/data/`.

- **Unidad de análisis y partición:** un cliente por fila (`id` único, 0 duplicados), así que se parte por fila, estratificada por `Response` (12,26 % de compradores en ambas partes): 304.887 clientes de entrenamiento y 76.222 de prueba cerrada, semilla 42. Los 5 pliegues de validación son los mismos en todas las etapas.
- **Hallazgos y decisiones:**
  - `Vehicle_Damage` y `Vehicle_Age` son texto con significado fijo → se pasan a 0/1 y 0/1/2 (la antigüedad conserva su orden).
  - El 17 % de las primas vale exactamente 2.630 (parece un mínimo impuesto) → se **marca** (`Premium_is_minimum`) sin cambiar la prima; el recorte de extremos aprende y va dentro del `Pipeline`.
  - Región es un código, no una cantidad → se trata como categoría (53 valores).
  - **`Policy_Sales_Channel` se elimina** (D13): es el canal de contacto y puede no conocerse antes de decidir a quién llamar (posible fuga). Cuesta ≈ 0,008 por cliente.
  - Lo que aprende de los datos (recortes, agrupar regiones raras, escalas) va dentro del `Pipeline` y se ajusta solo con el entrenamiento de cada pliegue, para evitar fuga.
- **Datos personales o sensibles:** no hay nombres ni documentos. `Gender` y `Age` son sensibles para la equidad: se conservan en el modelo y se auditan (sección 6).

## 3. Variables

> Fuente: `reports/04_features.md`.

Cada idea fue una hipótesis medida con la misma validación (5 pliegues), y se conservaba solo si mejoraba más de 1 vez el ruido entre pliegues y ganaba en 4 de 5.

- **Ninguna de las 5 ideas para agregar variables mejoró al modelo de árboles** (recorte de la prima, segmento comercial, edad como curva, tasa histórica de región, prima relativa a la región). Tampoco las 6 variables derivadas de la segunda ronda: la información útil ya está en las variables originales.
- **Una sola idea ganó, y solo para la regresión logística:** tratar la edad como curva sube la PR-AUC de 0,318 a 0,339 (6,8 veces el ruido; gana en los 5 pliegues), porque la aceptación dibuja una campana con la edad.
- **Retirar `Vintage` y `Driving_License` no cuesta nada medible** (0,3322 frente a 0,3326). Quitar además `Gender` tampoco, pero **el grupo decidió conservarla** (D12).
- **Quitar la prima sí empeora** al modelo de árboles (1,5 veces el ruido): se queda.
- **Conclusión:** el techo está en los datos, no en el modelado. Mejorar exige datos nuevos (historial de contactos, vencimiento del seguro actual, siniestros) **[P08]**.

## 4. Torneo de modelos

> Fuente: `reports/05_torneo.md`.

Cinco modelos y dos líneas base, con los mismos datos y pliegues y parámetros fijos:

| Modelo | Costo por cliente | Segundos de ajuste |
|---|---|---|
| **LightGBM** | **0,3326** | 2,5 |
| XGBoost | 0,3330 | 4,6 |
| **Regresión logística (edad como curva)** | 0,3352 | 1,8 |
| Bosque aleatorio | 0,3375 | 40,7 |
| Árbol de decisión | 0,3401 | 1,1 |
| Regla "llamar si hubo daño" | 0,3980 | — |
| No llamar a nadie | 0,6128 | — |

- **Finalistas: LightGBM y regresión logística.** LightGBM y XGBoost empatan en la práctica (0,46 veces el ruido) y se desempata por tiempo; la regresión cuesta ≈ 260 unidades más por 100.000 clientes pero es la única que se explica con una fórmula.
- **Se descartó el bosque aleatorio** (peor costo que la regresión en los 5 pliegues, 16 veces más lento, probabilidades peor calibradas) y el árbol (peor ordenamiento).
- **La elección no depende de R** (de 2 a 12, LightGBM y XGBoost son siempre los dos mejores).

## 5. Optimización y seguimiento

> Fuente: `reports/06_optimizacion.md`.

- **Diseño:** 20 ensayos por finalista (presupuesto fijado antes), 25 % de los clientes reservado y nunca visto por la búsqueda, y la regla de decisión escrita antes: se usan los parámetros optimizados solo si todo el intervalo del 95 % está por debajo de cero.
- **Resultado:** la búsqueda vio mejoras de 0,0013 (LightGBM) y 0,0020 (regresión), pero **en los clientes reservados los intervalos cruzan el cero** ([−0,0021; +0,0018] y [−0,0020; +0,0009]). Eran ruido (sesgo optimista): **se conservan los parámetros de partida**.
- **Umbral:** el teórico 1 ÷ (R + 1) = 16,7 % funciona; entre 15 % y 18 % el costo varía menos de 0,001. Llamar solo al 20 % cuesta ≈ 7.000 unidades más por 100.000 clientes y pierde el 44 % de los compradores.
- **Seguimiento:** 40 ejecuciones registradas en MLflow local (experimento `venta-cruzada-seguros-optimizacion`), cada una con parámetros, métricas y etiquetas.

## 6. Validación e interpretación

> Fuente: `reports/07_validacion.md`.

- **Decisiones congeladas antes de abrir la prueba** (2026-11-05 19:09, `reports/07_decisiones_congeladas.json`): LightGBM, parámetros de partida, sin calibrar (con clientes reservados, calibrar no mejora), costo con R = 5, umbral 16,7 %.
- **Resultado en la prueba (76.222 clientes, abierta una vez):** costo 0,3317 [0,3264; 0,3369]; baseline 0,3967 [0,3927; 0,4006]; diferencia −0,0650 [−0,0700; −0,0607]. PR-AUC 0,3533 frente a 0,2357; ROC-AUC 0,8519 frente a 0,7709. Coincide con la validación cruzada (0,3326).
- **Declaración:** la primera ejecución del cuaderno falló en el paso de SHAP por un error de código, después de abrir la prueba; se corrigió el error y se reejecutó sin cambiar el modelo.
- **Por segmento:** el recall es de 92 % a 98 % entre 26 y 65 años, pero de **33 % en 20-25 años y 30 % en 66 o más** (542 y 316 compradores sin oferta). Por género: se llama al 41,8 % de los hombres y al 29,6 % de las mujeres, con precisión parecida (29,9 % y 29,2 %).
- **Interpretación (SHAP):** pesan sobre todo `Previously_Insured` y `Vehicle_Damage`; luego región y edad. Límite: SHAP explica al modelo, no al mundo, y el daño como causa de compra es una hipótesis del negocio **[P09]**.
- **Carga de trabajo:** el modelo marca al 36,2 % de los clientes y compra el 12,3 %: ≈ 3 llamadas por comprador.

## 7. Registro del modelo

> Fuente: `reports/08_registro.md`, `models/ficha_modelo.md`.

- Modelo `workspace.default.venta_cruzada_seguros`, versión 1, alias `champion`, en **Databricks (Unity Catalog)**. Ida y vuelta comprobada: el modelo recuperado predice igual que el local.
- Exportado a `models/model.joblib` (capa `ServingModel` que traduce lo que escribe una persona a las columnas limpias) con su esquema en `models/input_schema.json`. Se comprobó que el archivo exportado da exactamente el costo medido en la prueba (0,331702).

## 8. Despliegue

> Fuente: `reports/09_despliegue.md`.

**[PENDIENTE]** Se despliega en la clase 5 (6 de noviembre). La app carga `models/model.joblib` desde el repositorio, no consulta Databricks, valida los datos (rechaza una edad de 200 con un mensaje claro) y trata "no sé" con valores neutros del entrenamiento. Probada en local con la prueba automática de Streamlit.

## 9. Riesgos, límites y siguientes pasos

- **Qué no hace el modelo:** no decide si se vende o se niega un seguro, no mide el efecto de llamar (los datos son históricos, no experimentales) y no explica por qué compran.
- **Límites de los datos:** un solo conjunto de una aseguradora, de época y país sin confirmar; licencia sin verificar **[P05]**.
- **Uso responsable:** usa edad y género; **Legal debe aprobar el género [D12]** y el grupo definir un piso de contacto para 20-25 y 66 o más **[P04]**. Retirar el género no habría garantizado equidad, y conservarlo exige la auditoría de la sección 6.
- **Supuestos por confirmar:** R = 5 **[P01]**, la capacidad de llamadas **[P02]**, si hay que explicar cada llamada **[P03]** (si sí, se despliega la regresión: cuesta ≈ 0,8 % más) y si el canal de venta se conoce antes de llamar **[P11]**.
- **Mejora candidata ya explorada:** la optimización de LightGBM con Optuna de Andiry (40 ensayos) bajó el costo de 0,3327 a 0,3303 en datos reservados (≈ 240 unidades por 100.000 clientes, del orden del ruido). No se adoptó porque se calculó sobre un entrenamiento con 649 clientes menos **[P12]** y la prueba cerrada ya se abrió con los parámetros de partida **[D14]**; podría validarse como mejora futura.
- **Siguiente mejora concreta:** conseguir datos nuevos (historial de contactos y vencimiento del seguro actual); vigilar en producción la tasa real de aceptación frente a la predicha y reentrenar si se aleja más de 10 % relativo durante 2 campañas (D11).

## Anexo: cómo reproducir el proyecto

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # en Mac/Linux: .venv/bin/python
# colocar el CSV de entrenamiento en data/raw/train.csv (o dataset.csv en la raíz)
# ejecutar en orden los notebooks 03_preprocesamiento a 09_inferencia (los 01 y 02 son de caso y EDA)
pytest                                  # 118 pruebas
streamlit run app/streamlit_app.py
```

Los datos crudos no se versionan. `data/processed/` se regenera con el cuaderno 03. El seguimiento de la etapa 6 está en `mlflow_local.db` (no se versiona) y el modelo final en Databricks: quien no tenga acceso regenera todo con los cuadernos 03 a 08, o usa `models/model.joblib`. Las credenciales van solo en `.env` (ignorado por Git).

---

### Lista de comprobación antes de entregar

- [x] Las **9 secciones** tienen contenido y cada decisión lleva su motivo (la 8 queda pendiente del despliegue).
- [x] Las cifras coinciden con `reports/07_validacion.md`.
- [ ] Completar integrantes, roles, nombre de la startup y enlace de la app.
- [x] No hay credenciales, `.env` ni datos personales.
- [ ] El enlace de la app abre en una ventana privada.
- [ ] Un tercero reproduce el proyecto con el anexo.
