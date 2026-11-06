# Modelo de datos: App con pestañas (`008-app-streamlit`)

La app no guarda nada; estas son las estructuras en memoria de `src/proyecto/reporting/`.

| Entidad | Campos | Origen |
|---|---|---|
| `Section` | `title` (texto sin `#`), `level` (2 a 4), `body` (markdown) | Un encabezado de un informe |
| `Pending` | `code` (`P01`…), `title`, `body`, `closed` (bool) | Subsección `### Pnn ·` de la sección B de `decisiones_del_grupo.md` |
| `MetricCard` | `label`, `value` (texto ya formateado), `help` (texto corto o vacío) | Bloque `prueba` de `07_metricas_test.json` |
| Tabla de segmentos | por variable (`Gender`, `Age`, `Region_Code`): columnas Segmento, Clientes, Costo, % que se llama, % real de interesados, Brecha, Recall | `07_segmentos.csv` |
| Fila de sensibilidad | `R`, costo del modelo, costo de la línea base, quién gana | `prueba.sensibilidad` del JSON |

Reglas: todo valor numérico mostrado proviene de un archivo; si falta, la entidad no se crea (no hay ceros por defecto).
