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
> Lo marcado **[DECIDE EL GRUPO]** no se puede saber desde los datos y no debe darse por aprobado.

- **Pregunta de negocio** (una frase, que alguien sin formación técnica entienda):
  _Hipótesis:_ ¿a qué clientes que ya tienen seguro de salud conviene ofrecerles también un seguro de vehículo? **[DECIDE EL GRUPO: confirmar o corregir]**
- **¿Quién usará el resultado y qué decisión tomará con él?**
  _Hipótesis:_ el equipo comercial, para decidir a quién llamar primero. **[DECIDE EL GRUPO]**
- **¿Qué cuesta equivocarse?** (cuál error es peor y por qué):
  **[DECIDE EL GRUPO]** No llamar a quien habría comprado es una venta perdida; llamar a quien no comprará es un costo de contacto. El grupo define cuál pesa más.

## 3. Datos

- **Fuente** (enlace de Kaggle, empresa, etc.): el esquema coincide con *Health Insurance Cross Sell Prediction* (Kaggle). **[DECIDE EL GRUPO: confirmar enlace]**
- **Filas / columnas:** `train.csv` 381.109 × 12; `test.csv` 127.037 × 11 (sin `Response`); `sample_submission.csv` es solo el formato de entrega.
- **Variable objetivo** (columna que queremos predecir o describir): `Response` (1 = el cliente aceptó la oferta).
- **Tipo de problema:** ☒ clasificación  ☐ regresión  ☐ clusterización
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☒ no  ☐ sí → la partición
  será por: fila, estratificada por `Response` (`id` es único; 0 filas duplicadas).
  Como `test.csv` no trae `Response`, la partición entrenamiento/validación/prueba se hace a partir de `train.csv`.
- **Datos personales o confidenciales presentes:** ☒ no  ☐ sí → no hay nombres ni documentos. `Gender` y `Age` son sensibles para la equidad (ver sección 5).
- **Licencia o permiso de uso de los datos:** **[DECIDE EL GRUPO: verificar la licencia en la fuente]**

## 4. Métrica

- **Métrica principal:** PR-AUC (propuesta)   **Por qué esa y no otra:** solo el 12,3 % de los clientes responde 1 (87,7 % / 12,3 %); la exactitud engaña.
- **Métricas secundarias:** recall entre el 10 % y el 20 % de clientes mejor puntuados; ROC-AUC. **[DECIDE EL GRUPO: confirmar]**
- **Línea base** (qué resultado obtiene una regla simple o un modelo trivial): decir siempre "no" acierta el 87,7 % y no encuentra a ningún comprador. Regla simple a superar: contactar solo a quien tiene `Vehicle_Damage = Yes` (23,8 % de ellos acepta, contra 0,5 % de quienes no).

## 5. Riesgos

- Fuga de información posible: no se ve una columna posterior a la decisión; conviene revisar `Vintage` (días como cliente) en la etapa 4.
- Sesgos o equidad: `Gender` y `Age`.
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
| | | |
