# Lista de calidad de la especificación: Registro del modelo (`006-registro-modelo`)

**Propósito:** comprobar que la especificación está completa antes de pasar al plan
**Creada:** 2026-11-05
**Especificación:** [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación innecesarios (se nombran MLflow, Databricks y archivos del proyecto porque la constitución y las etapas anteriores los fijaron)
- [x] Centrada en el valor: saber qué modelo se usa, en qué versión, y poder recuperarlo
- [x] Legible para alguien sin formación técnica
- [x] Secciones obligatorias completas

## Completitud de los requisitos

- [x] No quedan marcas [NEEDS CLARIFICATION]
- [x] Requisitos verificables y sin ambigüedad
- [x] Criterios de éxito medibles (ida y vuelta con tolerancia 1e-9, métricas iguales al JSON de la etapa 07)
- [x] Escenarios de aceptación definidos
- [x] Casos límite identificados (sin conexión, doble ejecución, falta el modelo, ida y vuelta que falla)
- [x] Alcance acotado (exportación a `model.joblib`, esquema de entrada y app quedan en la etapa 09)
- [x] Dependencias y supuestos identificados

## Preparación

- [x] Cada requisito tiene criterio de aceptación
- [x] El flujo principal está cubierto (conexión → registro → alias → ida y vuelta → constancia)
- [x] **Aprobación del grupo** (2026-11-05)

## Notas

- Elecciones del borrador que el grupo debe confirmar: nombre `venta_cruzada_lgbm`, experimento `venta-cruzada-registro`, y quitar `id`
  de la firma si el modelo predice sin ella.
