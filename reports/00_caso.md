# Ficha de caso

> **BORRADOR** preparado a partir de los datos. Estados de decisión: **[DECIDIDO]** (resuelto con evidencia del proyecto), **[ADOPTADO]** (propuesta vigente por defecto hasta que el grupo diga lo contrario) o **[PENDIENTE: dato externo]** (no se puede resolver con estos datos). Registro: `reports/decisiones_del_grupo.md`.
> Instrucciones y ejemplo completo: `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** `venta-cruzada-seguros`
- **business_question:** Una aseguradora ya tiene clientes con seguro de salud y quiere ofrecerles además un seguro de vehículo.
  El equipo comercial decide a qué clientes llamar primero, usando la edad, la antigüedad del vehículo, si ya tienen seguro de
  vehículo, si el vehículo tuvo daños, la prima anual, la región y el canal de venta. **[PENDIENTE: dato externo · P06]**
- **dataset_source:** el esquema coincide con *Health Insurance Cross Sell Prediction* (Kaggle). **[PENDIENTE: dato externo · P05]**
- **dataset_rows:** 381.109 en `train.csv` (más 127.037 en `test.csv`, sin objetivo)
- **dataset_columns:** 12 en `train.csv` (11 variables más `Response`)
- **target:** `Response` (1 = el cliente aceptó la oferta; 0 = no)
- **problem_type:** clasificación binaria
- **primary_metric:** PR-AUC (propuesta). Solo el 12,26 % de los clientes acepta, así que la exactitud engaña: un modelo que siempre
  dice "no" acierta el 87,7 % y no encuentra a ningún comprador. Se complementa con recall entre el 10 % y el 20 % de clientes mejor puntuados.
- **business_cost_note:** **[PENDIENTE: dato externo · P01]** No llamar a quien habría comprado es una venta perdida; llamar a quien no comprará es un
  costo de contacto. Como comprar es raro (1 de cada 8), dejar de contactar a un comprador suele ser el error más caro, pero el grupo debe confirmarlo.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
