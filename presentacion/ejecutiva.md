---
marp: true
theme: default
paginate: true
header: "Presentación ejecutiva · Venta cruzada de seguro de vehículo"
footer: "Casos Avanzados · Maestría en Ingeniería Analítica"
---

# 1 · Problema

- **¿Quién decide?** El gerente de la campaña comercial de una aseguradora.
- **¿Qué decide con el resultado?** A qué clientes con seguro de salud llamar primero para ofrecerles un seguro de vehículo.
- **¿Cuánto cuesta equivocarse?** Solo 1 de cada 8 clientes se interesa. No llamar a un interesado es una venta perdida; llamar a quien no se interesa es una llamada inútil. Suponemos que la venta perdida pesa **5 veces** una llamada inútil (por confirmar con la aseguradora).

> No llamar a nadie cuesta 0,613 por cliente y llamar a todos 0,877; con el modelo, 0,331. **La pregunta es a quién llamar primero**.

---

# 2 · Enfoque

- **Los datos:** 381.109 clientes de una aseguradora (conjunto público de Kaggle). Sin nombres ni documentos.
- **Cómo se validó con honestidad:** un cliente por fila, así que se parte por cliente. El 20 % se guardó como **prueba cerrada**; las decisiones se congelaron antes de abrirla y nada se cambió después de verla.
- **Qué se comparó y qué se eligió:** 5 modelos contra 2 reglas simples. Ganó **LightGBM**, con **5 variables nuevas** (por ejemplo, "sin seguro y con daño" o la distancia a la edad de mayor interés) y parámetros optimizados, comprobados en clientes que la búsqueda no vio.
- **Qué se descartó y por qué:** el canal de venta (puede no conocerse antes de llamar) y los modelos más lentos o más caros (random forest, árbol, regresión).

---

# 3 · Resultado y costo de negocio

| | Sin el modelo (regla: «sin seguro y con daño») | Con el modelo |
|---|---|---|
| Costo por cliente | 0,3720 | **0,3312** |
| Con 10.000 clientes | 3.720 unidades de llamada | **3.312** |

- **Mejora:** ≈ **408 unidades menos por cada 10.000 clientes (11 %)**. Intervalo del 95 % de la diferencia: de −0,045 a −0,036 por cliente, **todo por debajo de cero**.
- Llama al **36,5 %** de los clientes (la regla, al 47,8 %) y encuentra al **87,9 %** de los interesados.
- *Nota técnica:* PR-AUC 0,353 frente a 0,248 de la regla; ROC-AUC 0,852 frente a 0,785. Prueba con 76.222 clientes nunca vistos.
- *Transparencia:* el grupo evaluó dos modelos con esta misma prueba; este se eligió porque debía incluir las variables nuevas, no por su cifra.

---

# 4 · Demo de la app

**Enlace:** https://proyectoventacruzadasegur-fvvb72lfv96hczzujvoutd.streamlit.app/

1. **Un caso normal:** hombre de 34 años, sin seguro previo, con daño en el vehículo → el modelo da 39 % de probabilidad y recomienda **LLAMAR**.
2. **Un caso límite:** el mismo cliente con seguro previo y sin daño → 0,3 %, **NO LLAMAR**.
3. **Un dato inválido:** edad de 150 años → se rechaza: «Age: debe estar entre 18 y 100».

> Plan B: captura de pantalla con fecha y la app en local (`streamlit run app/streamlit_app.py`).

---

# 5 · Riesgos y siguientes pasos

- **Qué NO hace el modelo:** no decide si se vende o se niega un seguro; solo ordena a quién llamar. No mide el efecto de llamar.
- **Depende del supuesto 5 a 1:** si una venta perdida valiera 10 llamadas, la regla simple sería mejor. Hay que confirmarlo con el margen real.
- **Uso responsable:** el modelo usa **edad y género**. Encuentra solo a la mitad de los interesados de 18 a 29 años (y al 64 % de los mayores de 60): Legal debe aprobar el género y el negocio decidir si hay una campaña aparte para ellos.
- **Siguientes pasos:** registrar el modelo final en Databricks, conseguir datos nuevos (historial de contactos, vencimiento del seguro actual) y vigilar en producción la tasa real de interés frente a la predicha.
