# Ficha del modelo

> Actualizada el 2026-11-06 (`specs/007-integracion-main`) con el **modelo final**: el de la rama de la etapa 07 (5 variables nuevas,
> sin `Policy_Sales_Channel`, con `Gender`). Cifras de la prueba copiadas de `reports/07_metricas_test.json`; nada se recalculó.
> Un documento corto que cualquiera pueda leer antes de usar el modelo: qué es, con qué datos, qué rendimiento tiene
> y **qué no hay que hacer con él**.

## Qué es

Predice la probabilidad de que un cliente con seguro de salud se interese por un **seguro de vehículo**, para que el equipo comercial decida **a quién llamar primero**. No decide si se vende o se niega un seguro.

- **Modelo:** LightGBM con parámetros optimizados (Optuna, ensayo #13: 186 árboles, tasa de aprendizaje 0,0315, 31 hojas, `min_child_samples` 137, `subsample` 0,943, `colsample_bytree` 0,601, `reg_lambda` 0,478), con las variables nuevas y el preprocesamiento dentro de un solo `Pipeline` (`models/final_pipeline.joblib`). Sin calibrar (la calibración no mejoró; `reports/07_validacion.md`, sección 2).
- **Registro:** `workspace.default.venta_cruzada_seguros` **versión 2**, alias `champion` (Databricks, Unity Catalog; registrada el 2026-11-06). La versión 1 es el modelo anterior de `main`. La app usa el archivo `models/model.joblib` y no consulta Databricks.
- **Regla de decisión:** llamar si la probabilidad de interés supera **1 ÷ (R + 1) = 16,7 %**, con R = 5 (perder a un interesado cuesta 5 veces una llamada inútil; **hipótesis por confirmar, P01**). En la prueba equivale a llamar al 36,5 % de los clientes.

## Datos de entrenamiento

- **Fuente y licencia:** conjunto *Health Insurance Cross Sell Prediction* (Kaggle); el esquema y el tamaño coinciden. **Licencia sin confirmar (P05).**
- **Tamaño:** 381.109 clientes; 80 % para entrenar y 20 % (76.222) para la prueba. Del entrenamiento se quitaron 649 perfiles repetidos (mismo perfil y misma respuesta con distinto `id`, que aparecen al eliminar el canal; P12): quedan **304.238** clientes. La prueba se deja tal como llega.
- **Partición:** por cliente (un cliente por fila, `id` único), estratificada por `Response`, semilla 42. La prueba se abrió dos veces en el grupo, una por modelo (ver "Límites"); **este** modelo se evaluó una sola vez (2026-11-05 20:43).
- **Datos personales:** el dataset no trae nombres, documentos ni teléfonos. Se **elimina `Policy_Sales_Channel`** (posible fuga: puede no conocerse antes de llamar); `id` no entra al modelo.
- **Datos que pide la app (9):** edad, género, licencia de conducir, código de región, si ya tiene seguro de vehículo, antigüedad del vehículo, daño previo del vehículo, prima anual y días como cliente (`Vintage`).
- **Variables que el modelo calcula por su cuenta (5 nuevas):** sin seguro y con daño (`uninsured_with_damage`), daño × antigüedad del vehículo (`damage_x_vehicle_age`), cliente joven (`is_young_customer`, menos de 30 años), distancia a la edad de mayor interés (`age_peak_distance`, 42 años) y prima por año de edad (`premium_per_age`); además, la marca de prima mínima (`is_min_premium`, prima = 2.630).

## Rendimiento (prueba, 76.222 clientes nunca vistos; 12,26 % interesados)

Intervalos con *bootstrap* de clientes (1.000 remuestreos).

| Métrica | Valor | Intervalo del 95 % |
|---|---|---|
| **Costo por cliente (principal)** | **0,3312** | [0,3263; 0,3364] |
| Línea base: regla «llamar si no tiene seguro y tuvo daño» | 0,3720 | [0,3682; 0,3759] |
| Diferencia modelo − línea base | −0,0408 (≈ 408 llamadas inútiles ahorradas por cada 10.000 clientes) | [−0,0453; −0,0362] |
| PR-AUC | 0,353 (línea base 0,248\*) | no calculado |
| ROC-AUC | 0,852 (línea base 0,785\*) | no calculado |
| Recall de interesados / precisión | 87,9 % / 29,5 % | no calculado |
| % de clientes contactados | 36,5 % (línea base 47,8 %) | — |
| % de interesados al llamar al 20 / 30 / 50 % mejor puntuado | 56,4 / 77,9 / 98,9 % | — |

\* La regla solo da dos probabilidades distintas: sus métricas de ordenamiento son de referencia.

**Depende del supuesto R = 5:** con R = 3 el modelo sigue ganando (0,302 frente a 0,367); con R = 10 gana la regla (0,405 frente a 0,386).

## Variables que más pesan

`Previously_Insured` (quien ya tiene seguro de vehículo casi nunca se interesa), `uninsured_with_damage` y `Vehicle_Damage` (sin seguro y con daño previo) explican la mayor parte de la decisión; luego la edad (`age_peak_distance`, `Age`: interés en forma de campana con máximo entre 35 y 50 años), la antigüedad del vehículo y la región. `Gender` no está entre las 10 con más peso. Estas variables están correlacionadas y se reparten el crédito: el peso no es causa. (SHAP en 5.000 clientes de la prueba; `reports/07_validacion.md`, sección 5.)

## Límites y usos no recomendados

- **Datos con los que se entrenó:** un solo conjunto histórico de una aseguradora; no sabemos de qué época ni de qué país.
- **Supuestos de negocio de los que depende:** R = 5 (por confirmar; con R = 10 la regla de negocio es mejor); que los 9 datos se conozcan **antes** de llamar; y que el canal de venta **no** se conozca (se eliminó, **P11**).
- **Atributos sensibles o de uso regulado:** usa **`Gender` y `Age`** directamente (y `Region_Code`, posible sustituto de nivel socioeconómico). El grupo decidió conservar el género; **Legal debe aprobar su uso**. Por género, el modelo llama más a hombres (42,1 % frente a 29,9 %) en proporción a su interés real (14,0 % frente a 10,2 %), con recall parecido (89,8 % frente a 85,0 %). Por edad, **encuentra solo al 48,3 % de los interesados de 18 a 29 años y al 64,0 % de los de 60 o más**: compran poco, pero una parte importante de sus interesados no recibe la llamada (**P04**, política comercial). Detalle en `reports/07_segmentos.csv`.
- **La prueba en el grupo:** los mismos 76.222 clientes se usaron para evaluar dos modelos (19:09, modelo anterior de `main`; 20:43, este). Este modelo se eligió por un criterio fijado sin comparar cifras de prueba (incluir las variables nuevas, D15), y nada se ajustó después de verla; aun así, es una desviación de "abrir la prueba una sola vez" y se declara (`reports/07_validacion.md`, sección 3.1).
- **Qué NO debe hacerse con este modelo:** negar un seguro o fijar precios con él; excluir personas por edad o género; usarlo con otra población, otro país u otra época sin revalidar; tomar el «costo» como dinero sin confirmar R; leer SHAP como causa; reabrir la prueba para ajustarlo.
- **Lo que no se evaluó:** estabilidad en el tiempo, deriva de los datos, el modelo sin `Gender`, la calibración por segmento, otras regiones o aseguradoras y el efecto real de una campaña (el dataset es histórico, no experimental).

## Reproducibilidad

Código en `src/`, pruebas en `tests/` (`pytest`), notebooks en `notebooks/` (orden 03 → 09), decisiones en `reports/decisiones_del_grupo.md`, integración de las dos ramas del grupo en `reports/integracion_main.md`.
