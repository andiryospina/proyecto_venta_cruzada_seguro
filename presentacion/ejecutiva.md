---
marp: true
theme: default
paginate: true
header: "Presentación ejecutiva · Venta cruzada de seguro de vehículo"
footer: "Casos Avanzados · Maestría en Ingeniería Analítica"
---

# 1 · Problema

- **¿Quién decide?** El equipo comercial de una aseguradora.
- **¿Qué decide con el resultado?** A qué clientes con seguro de salud llamar primero para ofrecerles un seguro de vehículo.
- **¿Cuánto cuesta equivocarse?** Solo 1 de cada 8 clientes compra. No llamar a un comprador es una venta perdida; llamar a quien no comprará es una llamada inútil. Suponemos que la venta perdida pesa **5 veces** una llamada inútil (por confirmar con la aseguradora).

> Llamar a todos cuesta casi el doble que usar una regla simple; **la pregunta es a quién llamar primero**.

---

# 2 · Enfoque

- **Los datos:** 381.109 clientes de una aseguradora (conjunto público de Kaggle). Sin nombres ni documentos.
- **Cómo se validó con honestidad:** un cliente por fila, así que se parte por cliente. El 20 % se guardó como **prueba cerrada** y se abrió **una sola vez**, después de congelar las decisiones.
- **Qué se comparó y qué se eligió:** 5 modelos contra 2 reglas simples. Ganó **LightGBM**; la regresión logística queda como alternativa cuando haya que explicar cada llamada.
- **Qué se descartó y por qué:** 11 ideas de variables nuevas (no mejoraron nada), la optimización de parámetros (la mejora que vio la búsqueda era ruido) y el canal de venta (puede no conocerse antes de llamar).

---

# 3 · Resultado y costo de negocio

| | Sin el modelo («llamar si hubo daño») | Con el modelo |
|---|---|---|
| Costo por cliente | 0,3967 | **0,3317** |
| Con 100.000 clientes | 39.670 unidades de llamada | **33.170** |

- **Mejora:** ≈ **6.500 unidades menos por 100.000 clientes (16,4 %)**. Intervalo del 95 % de la diferencia: de −0,070 a −0,061 por cliente, **todo por debajo de cero**.
- Llama al 36 % de los clientes y encuentra al 87,5 % de los compradores.
- *Nota técnica:* PR-AUC 0,353 frente a 0,236 de la regla; ROC-AUC 0,852 frente a 0,771.

---

# 4 · Demo de la app

**Enlace:** *(se completa al desplegar, clase 5)*

1. **Un caso normal:** hombre de 34 años, sin seguro previo, con daño en el vehículo → el modelo da 39 % de probabilidad y recomienda **LLAMAR**.
2. **Un caso límite:** el mismo cliente con seguro previo y sin daño → 0,1 %, **NO LLAMAR**.
3. **Un dato inválido:** edad de 200 años → la app lo rechaza: «Age: debe estar entre 18 y 100».

> Plan B: captura de pantalla con fecha y la app en local (`streamlit run app/streamlit_app.py`).

---

# 5 · Riesgos y siguientes pasos

- **Qué NO hace el modelo:** no decide si se vende o se niega un seguro; solo ordena a quién llamar. No mide el efecto de llamar.
- **Límites de los datos:** un solo conjunto histórico de una aseguradora; licencia por confirmar.
- **Uso responsable:** el modelo usa **edad y género**. Casi no llama a menores de 26 ni a mayores de 65 (recall de 33 % y 30 %): Legal debe aprobar el género y el negocio definir si hay un piso de contacto.
- **Siguientes pasos:** conseguir datos nuevos (historial de contactos, vencimiento del seguro actual) y vigilar en producción la tasa real de aceptación frente a la predicha.
