# Venta cruzada inteligente: predicción del interés en seguro de vehículo

> Predecir qué clientes con seguro de salud aceptarán un seguro de vehículo, para que el equipo comercial priorice a quién llamar. _(Borrador: el grupo confirma el nombre y el caso.)_

**App desplegada:** [https://proyectoventacruzadasegur-fvvb72lfv96hczzujvoutd.streamlit.app/](https://proyectoventacruzadasegur-fvvb72lfv96hczzujvoutd.streamlit.app/) *(Streamlit Community Cloud; se despliega desde el fork `rigonzalezre-dot/proyecto_venta_cruzada_seguro`, rama `main`, idéntico al `main` de este repositorio)*

**Estado (2026-11-06):** etapas 1 a 9 completas en local. Modelo final: LightGBM con 5 variables nuevas, sin `Policy_Sales_Channel` y con `Gender`; costo 0,3312 por cliente en la prueba frente a 0,3720 de la regla "sin seguro de vehículo y con daño" (diferencia −0,0408, IC 95 % [−0,0453; −0,0362]). Ver [`reports/07_validacion.md`](reports/07_validacion.md), [`models/ficha_modelo.md`](models/ficha_modelo.md) y, sobre cómo se unieron las dos ramas del grupo, [`reports/integracion_main.md`](reports/integracion_main.md). Pendiente: registrar el modelo final en Databricks (T009 de `specs/006-registro-modelo`). Orden para reproducir: notebooks 03 a 09 y `pytest`.

## Qué contiene
Estructura obligatoria del curso. Cada carpeta tiene un propósito:

| Carpeta | Contenido |
|---|---|
| `.specify/` y `.claude/` | Entorno de IA: constitución del proyecto, Spec Kit (`/speckit-…`) y subagentes |
| `specs/` | Lo que genera Spec Kit: `spec.md`, `plan.md`, `tasks.md` de cada pieza (aparece al usarlo) |
| `especificaciones/` | Guías que se llenan **antes** de programar cada etapa |
| `data/raw/` | Datos originales, intocables |
| `data/processed/` | Datos limpios generados por el código |
| `notebooks/` | Un notebook por etapa; solo orquestan |
| `src/proyecto/` | Código reutilizable (data, features, models, tracking, inference) |
| `tests/` | Pruebas con `pytest` |
| `models/` | `final_pipeline.joblib` (modelo de la etapa 7), `model.joblib` e `input_schema.json` (para la app) y `ficha_modelo.md` |
| `app/` | `streamlit_app.py` |
| `reports/` | Una sección por hito e `informe_tecnico.md` |
| `presentacion/` | `ejecutiva.md` (máximo 5 diapositivas) |

## Cómo ejecutarlo
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # en Mac/Linux: .venv/bin/python
cp .env.example .env     # completa PROFILE o DATABRICKS_HOST y DATABRICKS_TOKEN
python scripts/check_databricks.py
pytest
streamlit run app/streamlit_app.py
```

## De dónde viene este repositorio
Nació de la rama `feature/estudiantes` del repositorio del curso (ver `LEEME-PRIMERO.md`): una persona del grupo la clonó con
`git clone --branch feature/estudiantes --single-branch …`, la apuntó a este repo con `git remote set-url origin …` y hizo `push`. Los demás integrantes
clonan **este** repositorio. Para arrancar, sigue `material-del-curso/guias/montaje-proyecto.md`.

## Equipo

**Repositorio:** https://github.com/andiryospina/proyecto_venta_cruzada_seguro

| Integrante | Rol |
|---|---|
| Ricardo González Restrepo (cuenta `rigonzalezre-dot`) | **[PENDIENTE: rol]** |
| Carolina Orejuela Perea | **[PENDIENTE: rol]** |
| Jessica Andiry Ospina Valencia | **[PENDIENTE: rol]** |
| Katherin Andrea Tabares | **[PENDIENTE: rol]** |
| Jhonatan Rojas Cardona | **[PENDIENTE: rol]** |

*Nombre de la startup:* **[PENDIENTE]**

Especificación del proyecto: [`especificacion-proyecto.md`](especificacion-proyecto.md) · Especificaciones por etapa: [`especificaciones/`](especificaciones/) · Decisiones del grupo y su estado: [`reports/decisiones_del_grupo.md`](reports/decisiones_del_grupo.md)
