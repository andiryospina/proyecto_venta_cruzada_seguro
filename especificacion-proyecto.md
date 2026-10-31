# Especificación del proyecto

> Plantilla. Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| | |
| | |
| | |

Nombre de la "startup": _______________   Repositorio (público): _______________

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
  información). `Gender` se evalúa en el análisis de equidad y el grupo decide si se usa como variable.
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
