# Portfolio Optimization in Python: Markowitz, Constraints & Sensitivity Analysis

Este proyecto implementa un modelo completo de optimización de portafolio financiero utilizando técnicas de programación convexa y análisis cuantitativo, orientado a entornos profesionales como fintechs, asset managers e inversores sofisticados.

## Objetivo
Construir, comparar y analizar distintos portafolios de inversión óptimos con base en métricas estadísticas reales:

1. Portafolio de **mínima varianza** (modelo clásico de Markowitz).
2. Portafolio que **maximiza retorno para una volatilidad dada**.
3. Portafolio con **restricciones prácticas** (sin cortos, límites por activo).
4. **Análisis de sensibilidad** ante cambios en las expectativas de retorno.
   
## Herramientas utilizadas

- **Python** · `numpy`, `pandas`, `cvxpy`
- **Datos financieros reales** extraídos con `yfinance`
- Análisis numérico puro (sin visualizaciones, centrado en lógica técnica)

## Qué resuelve el código

### Datos y estadística
- Importa precios ajustados de acciones reales (AAPL, MSFT, AMZN, GOOGL, META).
- Calcula retornos diarios, matriz de covarianza y correlación.
- Anualiza métricas para tomar decisiones de inversión a largo plazo.

### Optimización de portafolio
- Utiliza **programación convexa** para minimizar riesgo bajo distintas restricciones.
- Calcula **retorno esperado, volatilidad y ratio de Sharpe** para cada solución.
- Compara portafolios con y sin restricciones prácticas.

### Análisis de sensibilidad
- Simula un cambio en la expectativa de retorno de AAPL.
- Recalcula la asignación óptima de activos automáticamente.
- Evalúa el impacto de este cambio sobre el portafolio total.
- 
## Ejemplo de salida técnica

AAPL 0.1873
MSFT 0.2054
AMZN 0.2281
GOOGL 0.1984
META 0.1808
dtype: float64

Retorno 0.2273
Volatilidad 0.3149
Sharpe 0.6891

## Casos de uso reales

Este tipo de análisis puede aplicarse en:

- Creación de productos financieros algorítmicos.
- Gestión automatizada de carteras (robo-advisors).
- Modelado de riesgo en consultoría financiera.
- Presentaciones internas de equity research o departamentos de estrategia.

## Cómo usar

1. Abre este notebook en [Google Colab](https://colab.research.google.com/) o tu entorno local.
2. Ejecuta el código paso a paso.
3. Personaliza los activos o las restricciones según tus necesidades.
