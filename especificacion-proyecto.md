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

> **BORRADOR por confirmar en grupo.** Las cifras de las secciones 3 a 5 se midieron en `data/raw/train.csv`.
> Estados de decisión: **[DECIDIDO]** (resuelto con evidencia del proyecto), **[ADOPTADO]** (propuesta vigente por defecto hasta que el grupo diga lo contrario) o **[PENDIENTE: dato externo]** (no se puede resolver con estos datos). Lo pendiente no se puede saber desde los datos y no debe darse por aprobado. Registro: `reports/decisiones_del_grupo.md`.

- **Pregunta de negocio** (una frase, que alguien sin formación técnica entienda):
  _Hipótesis:_ ¿a qué clientes que ya tienen seguro de salud conviene ofrecerles también un seguro de vehículo? **[PENDIENTE: dato externo · P06]**
- **¿Quién usará el resultado y qué decisión tomará con él?**
  _Hipótesis:_ el equipo comercial, para decidir a quién llamar primero. **[PENDIENTE: dato externo · P06]**
- **¿Qué cuesta equivocarse?** (cuál error es peor y por qué):
  **[PENDIENTE: dato externo · P01]** No llamar a quien habría comprado es una venta perdida; llamar a quien no comprará es un costo de contacto. **Hipótesis vigente: la venta perdida pesa 5 veces una llamada inútil (R = 5).** Las etapas 5 y 6 mostraron que los finalistas y el umbral no cambian con R entre 2 y 12.

## 3. Datos

- **Fuente** (enlace de Kaggle, empresa, etc.): el esquema coincide con *Health Insurance Cross Sell Prediction* (Kaggle). **[PENDIENTE: dato externo · P05]** (el esquema y el tamaño, 381.109 × 12, coinciden con ese conjunto; falta confirmar enlace y autor en su página)
- **Filas / columnas:** `train.csv` 381.109 × 12; `test.csv` 127.037 × 11 (sin `Response`); `sample_submission.csv` es solo el formato de entrega.
- **Variable objetivo** (columna que queremos predecir o describir): `Response` (1 = el cliente aceptó la oferta).
- **Tipo de problema:** ☒ clasificación  ☐ regresión  ☐ clusterización
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☒ no  ☐ sí → la partición
  será por: fila, estratificada por `Response` (`id` es único; 0 filas duplicadas).
  Como `test.csv` no trae `Response`, la partición entrenamiento/validación/prueba se hace a partir de `train.csv`.
- **Datos personales o confidenciales presentes:** ☒ no  ☐ sí → no hay nombres ni documentos. `Gender` y `Age` son sensibles para la equidad (ver sección 5).
- **Licencia o permiso de uso de los datos:** **[PENDIENTE: dato externo · P05]** No se pudo verificar desde la fuente primaria; una referencia de terceros menciona GPL-2, **sin confirmar**. Revisar el campo *License* en la página del conjunto en Kaggle antes de publicar el repositorio.

## 4. Métrica

- **Métrica principal:** PR-AUC **[DECIDIDO · D01]** (para elegir variables y modelos; el costo por cliente es la métrica de negocio)   **Por qué esa y no otra:** solo el 12,3 % de los clientes responde 1 (87,7 % / 12,3 %); la exactitud engaña.
- **Métricas secundarias:** recall y *lift* en el 20 % mejor puntuado, ROC-AUC, log loss, Brier y costo por cliente con R = 5. **[DECIDIDO · D02]** (usadas de forma coherente en las etapas 4 a 6)
- **Línea base** (qué resultado obtiene una regla simple o un modelo trivial): decir siempre "no" acierta el 87,7 % y no encuentra a ningún comprador. Regla simple a superar: contactar solo a quien tiene `Vehicle_Damage = Yes` (23,8 % de ellos acepta, contra 0,5 % de quienes no).

## 5. Riesgos

- Fuga de información posible: `Policy_Sales_Channel` (canal de contacto) puede no conocerse antes de decidir a quién llamar; **se eliminó** (D13, **P11**). `Vintage` no mostró relación con el objetivo y se retiró (sin costo medible).
- Sesgos o equidad: `Gender` y `Age`. **`Gender` se conserva en el modelo** por decisión del grupo (D12), con auditoría por género y edad en la prueba cerrada (casi no se llama a menores de 26 ni a mayores de 65) y aprobación de Legal pendiente.
- Datos faltantes o de mala calidad: 0 nulos. En `Annual_Premium`, el 17 % de las filas vale exactamente 2.630 (parece un mínimo impuesto) y el máximo es 540.165 contra un percentil 99 de 72.963.
- Límites de lo que el modelo puede decir: ordena clientes por probabilidad de aceptar; no explica por qué compran ni mide el efecto de llamar.

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
| 2026-10-31 | Eliminar `Policy_Sales_Channel` (D13) | Posible fuga: puede no conocerse antes de llamar. Cuesta ≈ 800 unidades por 100.000 clientes |
| 2026-11-05 | Conservar `Gender` (D12) | Quitarla no tiene costo medible; el grupo decidió mantenerla. Exige auditoría de equidad y aprobación de Legal |
| 2026-11-05 | Modelo final: LightGBM con parámetros de partida, umbral 16,7 % (D08, D10) | La optimización no fue demostrablemente mejor; en la prueba cerrada cuesta 0,3317 frente a 0,3967 de la regla simple |
| 2026-11-05 | Registrar en MLflow local por ahora | No hay perfil de Databricks configurado; pendiente repetir el cuaderno 08 allá |
