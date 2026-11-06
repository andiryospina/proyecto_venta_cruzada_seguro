# Ficha del modelo

> Completada el 2026-11-05 con los resultados de la prueba de `reports/07_metricas_test.json`.
> Un documento corto que cualquiera pueda leer antes de usar el modelo: qué es, con qué datos, qué rendimiento tiene
> y **qué no hay que hacer con él**.

## Qué es

Predice la probabilidad de que un cliente con seguro de salud acepte un **seguro de vehículo**, para que el equipo comercial decida **a quién llamar primero**. No decide si se vende o se niega un seguro.

- **Modelo:** LightGBM (200 árboles, tasa de aprendizaje 0,08, 31 hojas), con el preprocesamiento dentro de un solo `Pipeline`. Parámetros de partida (la optimización no fue demostrablemente mejor).
- **Registro:** `workspace.default.venta_cruzada_seguros` versión 1, alias `champion` (Databricks, Unity Catalog). La app usa el archivo `models/model.joblib`, exportado de esa versión.
- **Regla de decisión:** llamar si la probabilidad de compra supera **1 ÷ (R + 1) = 16,7 %**, con R = 5 (perder a un comprador cuesta 5 veces una llamada inútil; **hipótesis por confirmar, P01**). Equivale a llamar a ≈ 36 % de los clientes.

## Datos de entrenamiento

- **Fuente y licencia:** conjunto *Health Insurance Cross Sell Prediction* (Kaggle); el esquema y el tamaño coinciden. **Licencia sin confirmar (P05).**
- **Tamaño:** 304.887 filas de 304.887 clientes para entrenar (80 %) y 76.222 para la prueba cerrada (20 %). Total 381.109.
- **Partición:** por cliente (un cliente por fila, `id` único), estratificada por `Response`, semilla 42; la prueba se abrió **una sola vez** (2026-11-05 19:09).
- **Datos personales:** el dataset no trae nombres, documentos ni teléfonos. Se **elimina `Policy_Sales_Channel`** (posible fuga: puede no conocerse antes de llamar) y no se usan `Vintage`, `Driving_License` ni `id`.
- **Variables del modelo (7 datos que pide la app):** edad, género, código de región, antigüedad del vehículo, daño previo del vehículo, si ya tiene seguro de vehículo y prima anual.

## Rendimiento (prueba, 76.222 clientes nunca vistos)

| Métrica | Valor | Intervalo del 95 % |
|---|---|---|
| **Costo por cliente (principal)** | **0,3317** | [0,3264; 0,3369] |
| Baseline: «llamar si hubo daño» | 0,3967 | [0,3927; 0,4006] |
| Diferencia modelo − baseline | −0,0650 (≈ 6.500 unidades de llamada ahorradas por 100.000 clientes, 16,4 %) | [−0,0700; −0,0607] |
| PR-AUC (control 1) | 0,3533 (baseline 0,2357) | no calculado |
| ROC-AUC (control 2) | 0,8519 (baseline 0,7709) | no calculado |
| Recall de compradores / precisión | 87,5 % / 29,6 % | no calculado |
| % de clientes contactados | 36,2 % (compra el 12,3 %) | — |

## Variables que más pesan

`Previously_Insured` (quien ya tiene seguro de vehículo casi nunca compra) y `Vehicle_Damage` (quien tuvo un daño compra mucho más) explican la mayor parte de la decisión; luego la región y la edad. El género y la prima aportan poco. (SHAP sobre la prueba; ver `reports/07_validacion.md`.)

## Límites y usos no recomendados

- **Datos con los que se entrenó:** un solo conjunto histórico de una aseguradora; no sabemos de qué época ni de qué país.
- **Supuestos de negocio de los que depende:** R = 5 (por confirmar); que los 7 datos se conozcan **antes** de llamar; y que el canal de venta **no** se conozca (se eliminó; si sí se conoce, el modelo mejoraría ≈ 800 unidades por 100.000 clientes, **P11**).
- **Atributos sensibles o de uso regulado:** usa **`Gender` y `Age`** directamente. El grupo decidió conservar el género (D12); **Legal debe aprobar su uso**. El modelo **casi no llama a menores de 26 ni a mayores de 65** (recall de 33 % y 30 %): compran poco, pero una parte importante de sus compradores no recibe la oferta (**P04**, política comercial).
- **Qué NO debe hacerse con este modelo:** negar un seguro o fijar precios con él; excluir personas por edad o género; usarlo con otra población, otro país u otra época sin revalidar; tomar el «costo» como dinero sin confirmar R; reabrir la prueba para ajustarlo.
- **Lo que no se evaluó:** estabilidad en el tiempo, deriva de los datos, otras regiones o aseguradoras y el efecto real de una campaña (el dataset es histórico, no experimental).

## Reproducibilidad

Código en `src/`, pruebas en `tests/` (`pytest`), notebooks en `notebooks/` (orden 03 → 09), decisiones en `reports/decisiones_del_grupo.md`.
