#Optimización de Producción Multiperíodo con Costes de Inventario

Este proyecto resuelve un problema de planificación de producción en entornos industriales utilizando programación lineal entera mixta (MILP). El objetivo es determinar cuántas unidades producir de cada producto en cada periodo, cumpliendo la demanda, respetando la capacidad de producción y minimizando el coste total (producción + inventario).

##Objetivo
- Cumplir la demanda prevista para varios periodos.
- Minimizar el coste total de producción e inventario.
- Respetar la capacidad máxima de producción en cada periodo.
- Planificar el inventario final de cada periodo.

##Técnicas aplicadas
- Modelado matemático en Python con PuLP.
- Programación lineal entera mixta (MILP).
- Simulación de demanda y parámetros si no se aportan datos.
- Generación automática de planes de producción e inventario.

##Tecnologías utilizadas
- Python 3.x
- pandas, numpy
- PuLP
- tabulate (para reportes tabulares)

##Estructura del proyecto
.
├── data/
│   ├── products.csv          # Datos de productos (costes, inventario inicial)
│   ├── demand.csv            # Demanda por producto y periodo
├── outputs/
│   ├── production_plan.csv   # Plan óptimo de producción
│   ├── inventory_plan.csv    # Inventarios finales proyectados
│   └── kpi_summary.md        # KPIs de coste y capacidad
└── scripts/
    └── master_production_schedule.py
