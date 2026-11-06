# Despliegue de la app

> **Parcial (2026-11-05).** Lo que se pudo preparar y probar en local está completo; lo que depende del despliegue real (enlace, ventana privada, ensayo cronometrado) sigue en blanco y se completa en la clase 5 (viernes 6 de noviembre).
> Guía paso a paso: `material-del-curso/guias/streamlit-despliegue.md` y `material-del-curso/kit/guia-despliegue-y-presentacion.md`.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | |
| Versión de Python elegida | ☐ 3.12  ☐ otra → motivo: _______________ |
| ¿Se comprobó en una **ventana privada**? | ☐ sí  ☐ no |
| ¿Se desplegó? | ☐ sí  ☐ no → **plan B** (apartado 4) |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | No se ponen credenciales en la nube y el despliegue no depende de la cuota de la plataforma. El archivo se exportó del `champion` (v1) y se comprobó que da el costo medido en la prueba (0,331702) |
| Versiones fijadas en `requirements.txt` | Para que la nube instale lo mismo que se probó (pandas 3.0.6, scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0, streamlit 1.66.0). El modelo es un archivo *pickle*: debe cargarse con las mismas versiones con que se guardó. Se agregó `pyarrow` porque los cuadernos leen Parquet |
| Qué NO se subió al repo (y por qué) | `data/raw/` (datos originales, licencia sin confirmar), `.env` (credenciales), `mlflow_local.db` y `models/final_pipeline.joblib` (pesados; la app usa solo `model.joblib`), y `holdout.parquet` (prueba cerrada) |
| La app traduce lo que escribe una persona (`ServingModel`) y rechaza datos imposibles con un mensaje claro | Un dato inválido nunca debe producir una respuesta silenciosa (`InputValidationError`) |

## 3. Pruebas del enlace público

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal | Hombre de 34 años, región 28, prima 31.000, vehículo de 1-2 años, con daño, sin seguro previo | LLAMAR | Probado en local: 39,3 % de probabilidad → LLAMAR. **Falta probar en el enlace público** |
| Límite (cambia la decisión) | El mismo cliente con seguro previo y sin daño | NO LLAMAR | Probado en local: 0,1 % → NO LLAMAR. **Falta probar en el enlace público** |
| Inválido (debe rechazarse con un mensaje claro) | Edad de 200 años | Error claro | Probado en local: «Age: debe estar entre 18 y 100». **Falta probar en el enlace público** |
| Con un campo en «No sé» | Edad y género en «no sé» | Responde con valores neutros | Probado en local: responde (35,6 % → LLAMAR). **Falta probar en el enlace público** |

## 4. Problemas encontrados y plan B

- Errores de despliegue que aparecieron y cómo se resolvieron (qué decía el registro y qué se cambió): _______________
- **Plan B** (si la app falla en vivo): captura con fecha y repo → **[PENDIENTE: tomar la captura al desplegar]**; app en local → `streamlit run app/streamlit_app.py` desde la raíz del repo
- Si **no se desplegó**: **plan de despliegue escrito** (qué se intentó, qué error dio, qué harían): _______________

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | |
| App (demo en vivo) | 4 min | |
| Resultados | 3 min | |
| Cierre | 1 min | |
| **Total** | **10 min** | |

- ¿Se pasó de 10 minutos? ☐ no  ☐ sí → qué se recortó: _______________
- Retroalimentación recibida (lo mejor y la corrección que propusieron): _______________
- **Corrección concreta que hicimos por ella:** _______________
- Quién habla de qué y quién responde las preguntas técnicas: _______________
