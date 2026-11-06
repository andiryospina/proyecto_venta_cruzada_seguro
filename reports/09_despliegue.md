# Despliegue de la app

> **Actualizado el 2026-11-06 (`specs/007-integracion-main`):** la app usa ahora el **modelo final de la rama** (LightGBM con las 5 variables
> nuevas, sin `Policy_Sales_Channel`, con `Gender`; formulario de 9 datos). Las cifras de las secciones 2 y 3 son de ese modelo.
>
> **Parcial (2026-11-05).** Lo que se pudo preparar y probar en local está completo; lo que depende del despliegue real (enlace, ventana privada, ensayo cronometrado) sigue en blanco y se completa en la clase 5 (viernes 6 de noviembre).
> Guía paso a paso: `material-del-curso/guias/streamlit-despliegue.md` y `material-del-curso/kit/guia-despliegue-y-presentacion.md`.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | https://proyectoventacruzadasegur-fvvb72lfv96hczzujvoutd.streamlit.app/ |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | `rigonzalezre-dot/proyecto_venta_cruzada_seguro` (fork de Ricardo, idéntico al `main` de `andiryospina/proyecto_venta_cruzada_seguro`), rama `main`, `app/streamlit_app.py`. Se despliega desde el fork porque Andiry es la dueña del repositorio oficial y Ricardo no tiene permisos de administrador allí |
| Versión de Python elegida | ☐ 3.12  ☐ otra → motivo: _______________ |
| ¿Se comprobó en una **ventana privada**? | ☐ sí  ☐ no |
| ¿Se desplegó? | ☒ sí (2026-11-06) — **falta comprobar el enlace en ventana privada y anotar las pruebas del apartado 3** |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | No se ponen credenciales en la nube y el despliegue no depende de la cuota de la plataforma |
| `model.joblib` se exporta de `models/final_pipeline.joblib` (etapa 7), **no** del registro | Desde el 2026-11-06 el alias `champion` apunta a la versión 2 (el modelo final), así que registro y archivo coinciden; la v1 es el modelo anterior de `main`. El notebook 09 comprobó que `model.joblib` da **las mismas probabilidades** que `final_pipeline.joblib` en 200 clientes de entrenamiento (diferencia máxima 0). La prueba **no** se volvió a abrir para esta comprobación |
| La decisión es la de menor costo esperado con la matriz `[[0, 1], [5, 0]]` | Equivale a llamar si P(interesado) > 1/6, la misma regla con que se evaluó el modelo en la etapa 7 |
| Versiones fijadas en `requirements.txt` | Para que la nube instale lo mismo que se probó (pandas 3.0.6, scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0, streamlit 1.66.0). El modelo es un archivo *pickle*: debe cargarse con las mismas versiones con que se guardó. Se agregó `pyarrow` porque los cuadernos leen Parquet |
| Qué NO se subió al repo (y por qué) | `data/raw/` (datos originales, licencia sin confirmar), `.env` (credenciales) y `mlflow_local.db`. **Sí** están versionados `models/final_pipeline.joblib` (681 KB; lo necesita el registro de la etapa 8) y `data/processed/train.parquet` y `test.parquet` (dataset público). Que la prueba esté en el repo no significa que se use: solo la etapa 7 la abrió |
| La app traduce lo que escribe una persona (`ServingModel`, `src/proyecto/inference/serving.py`) y rechaza datos imposibles con un mensaje claro | Un dato inválido nunca debe producir una respuesta silenciosa (`InputValidationError`). Hay dos barreras: el formulario no admite valores fuera del rango posible (edad 18–100, región 0–52 y entera, días como cliente 0–36.500, prima 1–10.000.000; definidos con su motivo en `INPUT_VALID_RANGE` de `config.py`; el tope de prima está pendiente de confirmar por el grupo) y, si un dato llega por otro camino, la función de predicción lo rechaza |
| Los "no sé" se rellenan con valores del entrenamiento | Mediana en los numéricos (edad 36, prima 31.725, región 28, 154 días) y valor más frecuente en los categóricos; calculados solo con `train.parquet` |

## 3. Pruebas del enlace público

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal | Hombre de 34 años, región 28, prima 31.000, 150 días como cliente, con licencia, vehículo de 1-2 años, con daño, sin seguro previo | LLAMAR | Probado en local (notebook 09): 39,1 % de probabilidad → LLAMAR. **Falta probar en el enlace público** |
| Límite (cambia la decisión) | El mismo cliente con seguro previo y sin daño | NO LLAMAR | Probado en local: 0,3 % → NO LLAMAR. **Falta probar en el enlace público** |
| Inválido (debe rechazarse con un mensaje claro) | Edad de 150 años | Error claro | Probado en local: la función de predicción responde «Age: debe estar entre 18 y 100»; en el formulario el campo de edad no admite más de 100. **Falta probar en el enlace público** |
| Con un campo en «No sé» | Edad y género en «no sé» | Responde con valores neutros | Probado en local: responde (36,7 % → LLAMAR). **Falta probar en el enlace público** |

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
