# EOQ Avanzado con Descuentos y Optimización Continua

Este proyecto resuelve el problema clásico de gestión de inventario utilizando el modelo **EOQ (Economic Order Quantity)**, extendido con:

- Descuentos por cantidad (precios variables por volumen)
- Optimización continua con `scipy.optimize`
- Comparativa de escenarios para tomar decisiones eficientes en retail

## Objetivo

Determinar de forma óptima:

- Cuántas unidades pedir (`Q`)
- Cuántas veces al año hacerlo
- Cómo minimizar el **coste total anual** considerando:
  - Coste de pedidos
  - Coste de mantenimiento de stock
  - Coste de adquisición (precio por unidad con descuentos)

## Técnicas aplicadas

- Modelo EOQ clásico
- EOQ con tramos de descuentos por cantidad
- Optimización continua del coste total con `scipy.optimize`
- Análisis profesional tabulado
- Visualización y análisis de sensibilidad (opcional)

## Tecnologías utilizadas

- Python 3.x
- Google Colab (recomendado)
- `pandas`, `numpy`, `scipy`, `tabulate`

## Estructura del proyecto

```bash
.
├── EOQ_avanzado.ipynb            # Notebook ejecutable
├── retail_store_inventory.csv    # Dataset de ejemplo
└── README.md                     # Este archivo
