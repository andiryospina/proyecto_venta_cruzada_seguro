# Guía rápida: probar la app con pestañas (`008-app-streamlit`)

Desde la raíz del repositorio, con el entorno del proyecto (`PYTHONUTF8=1`):

1. Pruebas: `python -m pytest -q --no-header -p no:cacheprovider` (todas en verde).
2. Arrancar: `streamlit run app/streamlit_app.py --server.headless true --server.port 8599` y abrir `http://localhost:8599/`.
3. Comprobar a mano:
   - Encima de las pestañas se ve **Avisos importantes** (prueba abierta dos veces, edad y género, pendientes).
   - Las 8 pestañas se abren y muestran su informe; "Resultado en la prueba" tiene tarjetas, dos imágenes y la tabla por segmentos.
   - "Decisiones y pendientes" muestra primero la sección B.
   - "Probar el modelo": pulsar **Evaluar** devuelve `LLAMAR` o `NO LLAMAR`.
4. Quitar un informe (por ejemplo, renombrar `reports/01_eda.md` en una copia) y ver que solo esa pestaña avisa.
5. Despliegue: el mismo entrypoint `app/streamlit_app.py`; no hay que cambiar nada en Streamlit Community Cloud.
