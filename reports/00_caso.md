# Ficha de caso

> Instrucciones y ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.
> Las cifras de esta ficha se calcularon sobre `dataset.csv` completo (descriptivas); el EDA las confirma.

- **case_id:** `venta-cruzada-seguro`

- **business_question:** Una aseguradora que ya vende **seguro de salud** quiere ofrecer a esos mismos
  clientes un **seguro de vehículo** (venta cruzada) por medio de su equipo comercial (llamadas y
  asesores). El equipo no puede contactar a toda la base y hoy elige a quién llamar sin una regla clara.
  Queremos un modelo que, con el perfil del cliente y de su vehículo, estime **la probabilidad de que el
  cliente esté interesado**, para que el **gerente de la campaña comercial** decida **a quién contactar
  primero**. El asesor conserva la conversación y la venta; el modelo solo ordena la lista.

- **dataset_source:** *Health Insurance Cross Sell Prediction* (Kaggle, autor Anmol Kumar), archivo de
  entrenamiento guardado en el repo como `dataset.csv`. **Licencia: por confirmar** en la página de Kaggle
  y con el instructor.

- **dataset_rows:** 381.109

- **dataset_columns:** 12 (`id` + 10 variables + objetivo). Sin valores faltantes. `id` es único por
  fila, así que **cada cliente aparece una sola vez**. Hay 269 filas idénticas en todo menos el `id`;
  el EDA decide qué hacer con ellas.

- **target:** `Response` (1 = el cliente se mostró interesado en el seguro de vehículo, 0 = no).
  Proporción: **12,26 % sí** (46.710) y **87,74 % no** (334.399).

- **problem_type:** clasificación binaria (desbalanceada)

- **primary_metric:**
  - **Métrica de negocio (principal): costo esperado por cliente** con la matriz de costos de abajo
    (menor es mejor). Incluye los dos tipos de error con su peso real para el negocio, cosa que la
    exactitud no hace.
  - **Métrica técnica (para comparar modelos en el torneo): PR-AUC (average precision)**. Mide qué tan
    bien el modelo pone a los interesados al principio de la lista, que es justo cómo se usa (ordenar a
    quién llamar). Se prefiere a ROC-AUC porque la clase positiva es solo el 12 %.
  - **Controles:** ROC-AUC, recall y precisión de la clase "sí" en el umbral elegido, y % de interesados
    capturados al contactar al 20 % / 30 % / 50 % de la base.
  - **La exactitud (accuracy) no se usa:** decir siempre "no" ya da 87,7 % y no encuentra a ningún interesado.

- **business_cost_note:** Equivocarse no cuesta lo mismo en las dos direcciones.
  - **No contactar a un cliente que sí estaba interesado** (falso negativo): se pierde la venta y la
    prima anual que habría pagado. Es el error **más caro**.
  - **Contactar a un cliente que no estaba interesado** (falso positivo): se pierde el tiempo de un
    asesor y se incomoda un poco al cliente. Cuesta poco y no deja daño duradero.
  - Matriz de costos (filas = lo que pasó, columnas = lo que predijo el modelo; unidades relativas).
    **La proporción 5 a 1 es un supuesto del grupo** que debe validarse con el margen real de una póliza
    frente al costo de una llamada; se reportará también la sensibilidad con 3 a 1 y 10 a 1.

    | real \ predicho | no contactar | contactar |
    |---|---|---|
    | **no interesado** | 0 | 1 |
    | **interesado** | 5 | 0 |

  - Con esa matriz se llama a un cliente cuando su probabilidad de interés supera **1/6 ≈ 0,167**
    (0,25 con 3 a 1; 0,091 con 10 a 1). El umbral final se elige en validación, nunca en prueba.
  - **Líneas base (costo esperado por cliente):** no llamar a nadie = 0,613; llamar a todos = 0,877;
    azar según proporciones = 0,645; **regla simple "sin seguro de vehículo previo y con daño previo"
    = 0,373** (contacta al 47,9 %, encuentra al 97,7 % de los interesados con precisión del 25 %).
    El modelo tiene que **bajar de 0,373** para que el negocio diga que sirve.

- **status:** borrador

- **reviewer_notes:**
