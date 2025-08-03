# Optimización de Turnos de Trabajo

## Contexto
Gestión de personal sanitario en centros asistenciales mediante programación lineal.  
El objetivo es asignar turnos reales a trabajadores disponibles minimizando solapamientos y cargas excesivas, respetando requisitos operativos.

## Datos
Se utilizaron datos reales de turnos semanales del sistema de Cleveland:
- **Archivo principal:** `cleveland_shifts.csv`
- **Periodo analizado:** 1 al 7 de octubre de 2021
- **Volumen:** 1447 turnos, 208 trabajadores únicos

## Técnicas utilizadas
- Modelado de programación lineal entera binaria (`pulp`)
- Preprocesamiento de datos reales
- Asignación óptima sujeto a:
  - Un trabajador por turno
  - Un turno por trabajador por día
  - Cobertura total de turnos

## Implementación

1. **Carga y limpieza de datos:**
   - Conversión de fechas
   - Cálculo de duración de cada turno
   - Selección de trabajadores activos en esa semana

2. **Formulación del modelo:**
   - Variables binarias `x[s, w]`: 1 si trabajador `w` cubre turno `s`
   - Restricciones:
     - Cada turno debe ser asignado a un solo trabajador
     - Un trabajador no puede estar en dos turnos solapados

3. **Resolución del modelo:**
   - Uso de `PULP_CBC_CMD` como solver
   - Extracción e interpretación de soluciones óptimas

## Resultados

- Total de turnos asignados: *[valor dinámico calculado]*
- Turnos correctamente cubiertos en el periodo analizado
- Asignación eficiente sin conflictos de horario
- Base sólida para escenarios más complejos (costes, descansos, preferencias)

## Valor aportado

Este proyecto simula una situación real que enfrentan hospitales y centros logísticos:  
organizar personal respetando carga legal y minimizando conflictos de planificación.  
Demuestra la capacidad para transformar datos operativos en soluciones optimizadas con impacto real.

## Posibles extensiones

- Restricciones legales (descansos mínimos, máximos semanales)
- Priorización de trabajadores frecuentes
- Costes asociados a ciertos turnos (nocturnos, festivos)
- Visualización de resultados (gráficos Gantt, calendarios)

**Tecnologías:** Python, pandas, PuLP  
**Categoría:** Optimización operativa / Recursos humanos / Planificación
