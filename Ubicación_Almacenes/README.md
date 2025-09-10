# Optimización de Ubicación de Almacenes con Capacidad

Este proyecto resuelve un problema clásico de localización de instalaciones (Capacitated Facility Location Problem) usando programación lineal entera mixta (MILP). El objetivo es seleccionar qué almacenes abrir y cómo asignar clientes, minimizando el coste total (fijo de apertura + transporte) y respetando la capacidad de cada almacén.

## Objetivo
- Decidir qué almacenes abrir entre un conjunto de ubicaciones candidatas.
- Asignar clientes a almacenes respetando su capacidad.
- Minimizar el coste total del sistema logístico.
- Reducir la distancia media de servicio ponderada por demanda.

## Técnicas aplicadas
- Modelado matemático con PuLP.
- Cálculo de distancias geográficas con fórmula de Haversine.
- Programación lineal entera mixta (MILP).
- Simulación de datasets realistas si no se proporcionan datos.

## Tecnologías utilizadas
- Python 3.x
- pandas, numpy
- PuLP
- haversine (cálculo de distancias geodésicas)

## Estructura del proyecto
.
├── data/
│   ├── facilities.csv        # Ubicaciones y capacidades de almacenes candidatos
│   ├── customers.csv         # Ubicaciones y demandas de clientes
├── outputs/
│   ├── facilities_open.csv   # Almacenes abiertos (1) / cerrados (0)
│   ├── assignment.csv        # Asignación óptima cliente-almacén
│   └── kpi_summary.md        # Resumen de métricas clave
└── scripts/
    └── facility_location.py
