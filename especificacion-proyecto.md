# Especificación del proyecto

> Plantilla. Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| Ricardo González Restrepo (cuenta `rigonzalezre-dot`) | Trabajo conjunto en todas las etapas del proyecto (según el grupo, 2026-11-06) |
| Carolina Orejuela Perea | Trabajo conjunto en todas las etapas del proyecto (según el grupo, 2026-11-06) |
| Jessica Andiry Ospina Valencia | Trabajo conjunto en todas las etapas del proyecto (según el grupo, 2026-11-06) |
| Katherin Andrea Tabares | Trabajo conjunto en todas las etapas del proyecto (según el grupo, 2026-11-06) |
| Jhonatan Rojas Cardona | Trabajo conjunto en todas las etapas del proyecto (según el grupo, 2026-11-06) |

Nombre del proyecto: **Venta cruzada inteligente: predicción del interés en seguro de vehículo**   Nombre de la "startup": **Contacto Inteligente**   Repositorio (público): https://github.com/andiryospina/proyecto_venta_cruzada_seguro

## 2. Caso de negocio

- **Pregunta de negocio** (una frase, que alguien sin formación técnica entienda):
  ¿A cuáles de nuestros clientes de seguro de salud debemos llamar primero para ofrecerles un seguro de vehículo?
- **¿Quién usará el resultado y qué decisión tomará con él?** El gerente de la campaña comercial, para
  decidir a quién contactar y en qué orden. El asesor hace la llamada y cierra la venta; el modelo solo
  ordena la lista.
- **¿Qué cuesta equivocarse?** (cuál error es peor y por qué): **no llamar a un interesado** (falso
  negativo) cuesta una venta y su prima anual; **llamar a un no interesado** (falso positivo) cuesta el
  tiempo de un asesor. Supuesto del grupo: el primero cuesta **5 veces** más que el segundo (se validará
  con el margen de una póliza frente al costo de una llamada; sensibilidad con 3 a 1 y 10 a 1).

## 3. Datos

- **Fuente** (enlace de Kaggle, empresa, etc.): *Health Insurance Cross Sell Prediction* (Kaggle, Anmol
  Kumar), archivo de entrenamiento guardado como `dataset.csv`.
- **Filas / columnas:** 381.109 / 12 (`id`, `Gender`, `Age`, `Driving_License`, `Region_Code`,
  `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage`, `Annual_Premium`, `Policy_Sales_Channel`,
  `Vintage`, `Response`). Sin valores faltantes.
- **Variable objetivo** (columna que queremos predecir o describir): `Response` (1 = interesado: 12,26 %;
  0 = no interesado: 87,74 %).
- **Tipo de problema:** ☒ clasificación (binaria, desbalanceada)  ☐ regresión  ☐ clusterización
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☒ no (`id` es único en las
  381.109 filas)  ☐ sí. La partición puede ser por fila, **estratificada por `Response`**. Hay 269 filas
  idénticas salvo el `id`; el EDA decide si se quitan antes de partir.
- **Datos personales o confidenciales presentes:** ☐ no  ☒ sí, de forma limitada: no hay nombres ni
  documentos, pero sí `Gender` y `Age` (atributos sensibles). `id` se quita del modelo (no aporta
  información). `Gender` se evalúa en el análisis de equidad; **el grupo decidió conservarla en el modelo** (2026-11-05), con auditoría por género y edad (`reports/07_segmentos.csv`) y aprobación de Legal pendiente.
- **Licencia o permiso de uso de los datos:** por confirmar en la página de Kaggle y con el instructor.

## 4. Métrica

- **Métrica principal:** **costo esperado por cliente** con la matriz `[[0, 1], [5, 0]]` (filas = real
  no/sí, columnas = predicho no contactar/contactar; menor es mejor). **Por qué esa y no otra:** refleja
  que perder un interesado cuesta 5 veces más que una llamada sin éxito; la exactitud no lo ve (decir
  siempre "no" da 87,7 %). **Métrica técnica para el torneo de modelos: PR-AUC (average precision)**,
  porque mide si los interesados quedan al principio de la lista y es sensible con solo 12 % de positivos.
- **Métricas secundarias:** ROC-AUC; recall y precisión de la clase "sí" en el umbral elegido; % de
  interesados capturados al contactar al 20 %, 30 % y 50 % de la base.
- **Línea base** (qué resultado obtiene una regla simple o un modelo trivial): costo esperado por cliente
  — no llamar a nadie 0,613; llamar a todos 0,877; azar 0,645; **regla "sin seguro de vehículo previo y
  con daño previo" 0,373** (contacta al 47,9 %, recall 97,7 %, precisión 25,0 %). Para PR-AUC, un modelo
  sin información obtiene ≈ 0,123 (la proporción de positivos). Cifras calculadas sobre todo el dataset;
  se recalculan sobre validación.

## 5. Riesgos

- Fuga de información posible: `Response` se registró después del contacto; ninguna otra columna lo
  describe directamente. **`Policy_Sales_Channel` se eliminó del modelo (2026-10-31).** `Vintage` (días como cliente) y `Policy_Sales_Channel` (canal de contacto) se
  revisan en el EDA para confirmar que se conocen **antes** de decidir a quién llamar. El umbral se elige
  en validación, nunca en prueba.
- Sesgos o equidad: el modelo podría contactar menos a ciertos grupos de edad, género o región. Se
  revisan las tasas de contacto y el recall por `Gender`, por rangos de `Age` y por `Region_Code`.
- Datos faltantes o de mala calidad: no hay faltantes. `Annual_Premium` tiene una cola larga (mediana
  31.669, máximo 540.165) y un valor mínimo repetido (2.630) que hay que investigar. `Driving_License = 0`
  en solo 812 filas. `Region_Code` (53 valores) y `Policy_Sales_Channel` (155 valores) son códigos, no
  números. 269 filas duplicadas salvo el `id`.
- Límites de lo que el modelo puede decir: estima **interés declarado**, no compra efectiva. No explica
  por qué un cliente se interesa (correlación, no causa) y no sirve para fijar precios. Decide el orden
  de la lista, no si el cliente recibe o no el seguro.

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha aprobada, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final (hasta 8 días tras la última clase) | Domingo 15 nov |

## 7. Decisiones tomadas (agréguenlas a medida que avancen)

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-31 | Métrica de negocio: costo esperado por cliente con matriz 5 a 1 (supuesto) | Perder un interesado cuesta más que una llamada sin éxito; la exactitud ignora esa diferencia |
| 2026-10-31 | Métrica técnica: PR-AUC; controles ROC-AUC, recall/precisión y captura al 20/30/50 % | El modelo se usa para ordenar una lista y la clase positiva es solo el 12 % |
| 2026-10-31 | Línea base a superar: regla "sin seguro previo y con daño" (costo 0,373) | Es la mejor estrategia sin modelo de las evaluadas |
| 2026-10-31 | Prima alta: recortar al p99,9 de entrenamiento + `log1p`; no borrar filas | La cola alta es real: esos clientes se interesan más (15–17 %) |
| 2026-10-31 | Prima 2.630 = prima mínima del producto: conservar + `is_min_premium` | Input de negocio; 17 % de los clientes |
| 2026-10-31 | Clientes sin licencia (654) se conservan | Input de negocio: pueden asegurar un vehículo que conduce otra persona |
| 2026-10-31 | Partición 80/20 estratificada por `Response`, semilla 42; repetidos fuera solo en entrenamiento | 1 fila = 1 cliente; conserva el 12,26 % de interesados |
| 2026-10-31 | Eliminar `Policy_Sales_Channel` del modelo | Es el canal de contacto: puede no conocerse antes de decidir a quién llamar (posible fuga). Se pierde una señal media (V de Cramér 0,263) |
| 2026-10-31 | Crear 5 variables nuevas en `features/engineering.py` (`uninsured_with_damage`, `damage_x_vehicle_age`, `is_young_customer`, `age_peak_distance`, `premium_per_age`), apagadas por defecto | Salen de la relación con la respuesta del EDA; solo entran al modelo si en la etapa 04 mejoran más que el ruido entre pliegues |
| 2026-10-31 | Etapa 04: ninguna variable nueva pasa la regla mejora / ruido > 1 con LightGBM (máx. 0,24, `premium_per_age`); aun así el torneo las usa | Decisión del grupo: pueden ayudar a la regresión logística y al árbol, que no descubren interacciones solos; para LightGBM el efecto es nulo (`reports/04_features.md`) |
| 2026-10-31 | Torneo: finalistas **LightGBM** (costo 0,3324) y **XGBoost** (0,3329, empatados: diferencia / ruido 0,50) | Los 5 modelos vencen a la regla de negocio (0,3729) en 5 de 5 pliegues; random forest empata pero es 11 veces más lento (`reports/05_torneo.md`) |
| 2026-10-31 | **Modelo elegido: LightGBM** (pasa solo a la optimización) | Costo más bajo (0,3324) y el más rápido de los tres de árboles en conjunto (2,4 s por pliegue); XGBoost queda como referencia |
| 2026-11-05 | Optimización de LightGBM (40 ensayos de Optuna, métrica: costo de negocio, umbral 1/6 fijo): **se usan los parámetros optimizados** (`reports/06_best_params.json`) | En los 76.060 clientes reservados el costo baja de 0,3327 a 0,3303 (−0,0024; IC 95 % [−0,0042; −0,0006], todo bajo cero, como pedía la regla escrita antes). Mejora real pero pequeña (`reports/06_optimizacion.md`) |
| 2026-11-05 | Regla de calibración enmendada **antes de ejecutar**: calibrar solo si todo el IC 95 % de (log loss calibrado − sin calibrar) está bajo cero **y** el costo no sube | La primera versión aceptaba cualquier baja del log loss, aunque fuera ruido; se usa el mismo criterio que en la etapa 06 (`specs/005-validacion/spec.md`) |
| 2026-11-05 | **No se calibran las probabilidades** | En la reserva de la etapa 06: log loss −0,00008, IC 95 % [−0,00025; +0,00010] (cruza el cero) y costo +0,0001; no se cumple ninguna condición. Decisiones congeladas a las 20:43:52, antes de abrir la prueba (`reports/07_validacion.md`) |
| 2026-11-05 | **Prueba abierta una sola vez** (20:43:56, 76.222 clientes): el modelo **supera a la regla de negocio** con confianza del 95 % | Costo 0,3312 frente a 0,3720; diferencia −0,0408, IC 95 % [−0,0453; −0,0362], todo bajo cero. Llama al 36,5 % de la base (la regla, al 47,8 %) con recall 87,9 % (`reports/07_validacion.md`) |
| 2026-11-05 | Límites declarados, sin cambiar el modelo: con costo 10 a 1 gana la regla (0,386 frente a 0,405); recall bajo en 18–29 años (48 %) y 60+ (64 %); `Age`, `Gender` y `Region_Code` son atributos sensibles | Cambiar modelo o umbral mirando la prueba la invalidaría. Pendiente con validación: confirmar el supuesto 5 a 1 y medir el modelo sin `Gender` |
| 2026-11-05 | La ejecución de la etapa 07 quedó en **MLflow local**, no en Databricks | El `.env` de quien ejecutó tenía `MLFLOW_FORCE_LOCAL` y la conexión comentada; no se repite porque sería abrir la prueba otra vez. Las cifras están en `reports/07_metricas_test.json` |
| 2026-11-05 | *(desde `main`)* Conservar `Gender` en el modelo (D12 del registro del grupo) | Quitarla no tiene costo medible; el grupo decidió mantenerla. Exige auditoría de equidad (hecha en la etapa 07) y aprobación de Legal |
| 2026-11-05 | *(desde `main`, **reemplazada el 2026-11-06**)* Modelo final: LightGBM con parámetros de partida y sin variables nuevas (D14) | Reemplazada por la decisión del 2026-11-06 (D15). Ese modelo también se evaluó en la prueba (19:09) |
| 2026-11-05 | *(desde `main`)* Registrar el modelo final en Databricks (Unity Catalog, alias `champion`); la app usa `models/model.joblib` y no consulta Databricks | El registro es la fuente de verdad. `champion` apunta desde el 2026-11-06 a la **versión 2**, el modelo final (T009 de `specs/006-registro-modelo`); la versión 1 es el modelo anterior de `main` |
| 2026-11-06 | **Integración de `main`: el modelo final es el de esta rama (D15)** — LightGBM con las 5 variables nuevas, sin `Policy_Sales_Channel`, con `Gender`, parámetros de Optuna. Código oficial de `src/` = el de esta rama | El grupo exige incluir las variables nuevas. No se eligió comparando cifras de prueba. La prueba quedó abierta dos veces en el grupo (19:09 y 20:43 del 2026-11-05) y se declara (`reports/07_validacion.md` §3.1). Detalle: `reports/integracion_main.md` |
| 2026-11-06 | El modelo se registra como `venta_cruzada_seguros` (nombre que ya usaba el grupo), no `venta_cruzada_lgbm` | Un solo nombre en el registro; la versión 1 de `main` queda como historia |
