# Lista de calidad de la especificación: Validación final (`005-validacion`)

**Propósito:** comprobar que la especificación está completa antes de pasar al plan
**Creada:** 2026-11-05
**Especificación:** [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación innecesarios (se nombran archivos y herramientas del proyecto porque el grupo los fijó en etapas anteriores)
- [x] Centrada en la decisión de negocio (a quién llamar y cuánto cuesta)
- [x] Legible para alguien sin formación técnica
- [x] Secciones obligatorias completas

## Completitud de los requisitos

- [x] No quedan marcas [NEEDS CLARIFICATION]
- [x] Requisitos verificables y sin ambigüedad
- [x] Criterios de éxito medibles
- [x] Escenarios de aceptación definidos
- [x] Casos límite identificados (prueba abierta dos veces, intervalo que cruza cero, calibración que mejora log loss pero sube el costo)
- [x] Alcance acotado (registro, exportación y app quedan fuera)
- [x] Dependencias y supuestos identificados

## Preparación

- [x] Cada requisito tiene criterio de aceptación
- [x] El flujo principal está cubierto (calibración → prueba → segmentos)
- [x] **Aprobación del grupo** (2026-11-05)

## Notas

- Elecciones del borrador que el grupo debe confirmar antes de abrir la prueba: tramos de edad (18–29, 30–44, 45–59, 60+) y mínimo de
  1.000 clientes por región para mostrarla aparte.
