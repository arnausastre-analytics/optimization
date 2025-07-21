# 🚚 Optimización de rutas de entrega para eCommerce basado en datos reales

## 📦 Contexto del proyecto

En un entorno de comercio electrónico con entregas de última milla, **la optimización de rutas logísticas es clave para reducir costes, mejorar la eficiencia y garantizar la satisfacción del cliente**.  
Este proyecto utiliza datos reales del marketplace brasileño **Olist** (región metropolitana de São Paulo) para simular y resolver un problema de ruteo de vehículos (**Vehicle Routing Problem - VRP**) en un escenario realista.

El objetivo es que empresas de eCommerce puedan, en base a los pedidos diarios que reciban, **planificar sus rutas de entrega de forma óptima y respetando restricciones operativas realistas**.

---

## 🎯 Objetivos

✅ Diseñar un modelo de optimización que permita:

- **Minimizar el coste total operativo** (en función de distancias y tiempo).
- Cumplir **restricciones realistas** como:
  - Tiempo máximo de trabajo diario por repartidor.
  - Número máximo de entregas por vehículo/ruta.
  - Servicio completo a todos los clientes planificados.
- Facilitar que la empresa pueda **configurar el número de pedidos diarios que desea optimizar**.

---

## 🔧 Técnicas y herramientas

- 📈 **Análisis de datos y simulación realista de operaciones logísticas**.
- 🧩 **Modelado matemático del VRP con restricciones**:
  - `OR-Tools` (Google Operations Research Tools).
- 🗺️ **Visualización geográfica**:
  - `Folium` / `Plotly` para representar las rutas optimizadas sobre mapas interactivos.

---

## 🔐 Restricciones modeladas

- **Velocidad media asumida**: 30 km/h (tráfico urbano São Paulo).
- **Tiempo promedio de servicio en cliente**: 8 minutos por entrega.
- **Número máximo de entregas por ruta**: configurable (ejemplo: 20 pedidos/ruta).
- **Tiempo máximo por ruta**: configurable (ejemplo: 480 minutos = 8 horas).
- **Cada cliente debe ser atendido exactamente una vez**.
- **Inicio y fin de cada ruta en el almacén central**.

---

## 📂 Estructura del repositorio

optimization_routing/
│
├── README.md <-- Este documento
├── data/
│ └── raw/ <-- Archivos originales de Olist
│ └── processed/ <-- Datos filtrados y preparados
│
├── notebook/
│ └── routing_optimization.ipynb <-- Notebook principal en Google Colab
│
├── scripts/
│ └── utils.py <-- Funciones auxiliares para procesamiento
│
└── requirements.txt <-- Dependencias necesarias




---

## 📊 Visualización de resultados

El proyecto incluye:

- Mapas interactivos con las rutas optimizadas.
- Resumen de métricas clave:
  - Distancia total recorrida.
  - Tiempo total de operación.
  - Número de vehículos/rutas utilizados.
  - Coste total estimado.

---

## 🔔 Instrucciones de uso

1️⃣ Subir datos originales Olist a `data/raw/`.

2️⃣ Ejecutar notebook `routing_optimization.ipynb`:
- Filtrado automático de pedidos de São Paulo.
- Configuración manual del número de pedidos a optimizar y parámetros clave:
  - Tiempo máximo/ruta
  - Nº máximo de entregas/ruta

3️⃣ Visualizar y exportar resultados.

---

## 💡 Posibles extensiones futuras

- Modelado de **ventanas horarias** (VRPTW).
- Restricciones adicionales de capacidad (peso/volumen).
- Diferenciación de zonas urbanas/rurales en costes o velocidades.

---

## 📥 Dataset original

- **Brazilian E-Commerce Public Dataset by Olist**:  
  https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

---

## 👨‍💼 Autor

[Tu Nombre]  
*Data Analyst & Machine Learning Consultant*  
🔗 [LinkedIn](https://www.linkedin.com) | [GitHub](https://github.com)

---

