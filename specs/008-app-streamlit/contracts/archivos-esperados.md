# Contrato: archivos que la app espera (`008-app-streamlit`)

## Lo que la app espera de los archivos

| Archivo | Lo que debe tener | Si no lo tiene |
|---|---|---|
| `reports/07_metricas_test.json` | `prueba.modelo` con `cost`, `cost_ic95`, `contact_rate`, `recall`, `precision`, `pr_auc`, `roc_auc`, `capture_20`; `prueba.linea_base.cost`; `prueba.diferencia_costo` (`valor`, `ic95`); opcional `prueba.sensibilidad` | Se omiten las tarjetas que no se pueden armar |
| `reports/07_validacion.md` | Un encabezado cuyo título empieza por `3.1` | Se muestra el informe sin destacar la sección y se avisa |
| `models/ficha_modelo.md` | `## Límites y usos no recomendados` con viñetas que empiezan por `Atributos sensibles` y `La prueba en el grupo` | Se muestra la sección completa; si no existe, un aviso |
| `reports/decisiones_del_grupo.md` | `## B. …` con `### Pnn · …` | Se muestra el archivo completo y un aviso |
| `reports/07_segmentos.csv` | Columnas `variable, segment, clients, cost, contact_rate, positive_rate, gap_contact_vs_real, recall` | Se omite la tabla y se avisa |
| `reports/prueba_abierta.txt` | Texto libre | Se omite ese aviso |

## Lo que la app promete

- Nunca lanza excepción por un archivo ausente o con formato inesperado.
- Nunca escribe en el repositorio ni lee `.env`.
- No cambia `models/input_schema.json`: el formulario sigue construyéndose con él.
