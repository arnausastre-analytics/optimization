# scripts/facility_location.py
# ==============================================================
# Capacitated Facility Location (MILP con PuLP)
# --------------------------------------------------------------
# Entradas opcionales (./data):
#  - facilities.csv -> id,lat,lon,capacity_units,fixed_open_cost
#  - customers.csv  -> id,lat,lon,demand_units
#
# Si no existen, se simula un caso reproducible.
#
# Parámetros CLI:
#  --cost-per-km-unit  : coste de transporte (€/unidad·km)
#  --max-facilities    : límite de almacenes a abrir (opcional)
#  --max-service-km    : radio máx de servicio (km, opcional; si se da,
#                        bloquea asignaciones más lejanas)
#  --time-limit        : límite de tiempo del solver (s)
#
# Salidas (./outputs):
#  - assignment.csv        -> q[i,j] unidades servidas i<-j
#  - facilities_open.csv   -> y[j] almacenes abiertos
#  - kpi_summary.md        -> métricas clave
# ==============================================================

import os
import sys
import math
import argparse
import random
from dataclasses import dataclass
from typing import Tuple, Dict

import numpy as np
import pandas as pd

try:
    import pulp as pl
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pulp"])
    import pulp as pl

SEED = 7
random.seed(SEED)
np.random.seed(SEED)


# -------------------- Utilidades --------------------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Distancia geodésica en km (Haversine)."""
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def load_or_simulate(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carga CSVs si existen; si no, simula un caso realista."""
    ensure_dir(data_dir)
    f_path = os.path.join(data_dir, "facilities.csv")
    c_path = os.path.join(data_dir, "customers.csv")

    if os.path.exists(f_path) and os.path.exists(c_path):
        fac = pd.read_csv(f_path)
        cus = pd.read_csv(c_path)
        return fac, cus

    # --- Simulación: ciudad genérica alrededor de (lat,lon) ---
    print("[i] No se encontraron CSVs. Generando dataset simulado en ./data ...")
    center_lat, center_lon = 40.4168, -3.7038  # Madrid centro (solo referencia)

    # Almacenes candidatos
    n_fac = 7
    fac = []
    for j in range(n_fac):
        lat = center_lat + np.random.uniform(-0.7, 0.7)
        lon = center_lon + np.random.uniform(-0.7, 0.7)
        capacity = np.random.randint(800, 1400)
        fixed = np.random.randint(9000, 16000)
        fac.append((f"F{j+1}", lat, lon, capacity, fixed))
    fac = pd.DataFrame(fac, columns=["id", "lat", "lon", "capacity_units", "fixed_open_cost"])

    # Clientes / zonas de demanda
    n_cus = 60
    cus = []
    for i in range(n_cus):
        lat = center_lat + np.random.uniform(-1.0, 1.0)
        lon = center_lon + np.random.uniform(-1.0, 1.0)
        demand = np.random.randint(10, 60)
        cus.append((f"C{i+1}", lat, lon, demand))
    cus = pd.DataFrame(cus, columns=["id", "lat", "lon", "demand_units"])

    fac.to_csv(f_path, index=False)
    cus.to_csv(c_path, index=False)
    print("[i] Dataset simulado guardado en ./data")
    return fac, cus


# -------------------- Modelo MILP --------------------
@dataclass
class SolveResult:
    status: str
    total_cost: float
    fixed_cost: float
    transport_cost: float
    open_facilities: pd.DataFrame
    assignment: pd.DataFrame
    kpis: Dict[str, float]


def build_and_solve(
    fac: pd.DataFrame,
    cus: pd.DataFrame,
    cost_per_km_unit: float = 0.35,
    max_facilities: int = None,
    max_service_km: float = None,
    time_limit: int = 120
) -> SolveResult:

    F = fac["id"].tolist()
    C = cus["id"].tolist()

    # Parámetros
    capacity = fac.set_index("id")["capacity_units"].to_dict()
    fixed_cost = fac.set_index("id")["fixed_open_cost"].to_dict()
    demand = cus.set_index("id")["demand_units"].to_dict()

    # Matriz de distancias
    dist: Dict[Tuple[str, str], float] = {}
    for i, r_i in cus.set_index("id").iterrows():
        for j, r_j in fac.set_index("id").iterrows():
            d = haversine_km(r_i["lat"], r_i["lon"], r_j["lat"], r_j["lon"])
            dist[(i, j)] = d

    # Costo de transporte por unidad
    transp_cost = {(i, j): cost_per_km_unit * dist[(i, j)] for i in C for j in F}

    # Modelo
    mdl = pl.LpProblem("CapacitatedFacilityLocation", pl.LpMinimize)

    # Variables:
    # y_j = 1 si se abre el almacén j
    # q_ij >= 0 unidades enviadas del almacén j al cliente i
    y = pl.LpVariable.dicts("y", F, lowBound=0, upBound=1, cat=pl.LpBinary)
    q = pl.LpVariable.dicts("q", (C, F), lowBound=0, cat=pl.LpContinuous)

    # Objetivo: costes fijos + transporte
    mdl += (
        pl.lpSum(fixed_cost[j] * y[j] for j in F) +
        pl.lpSum(transp_cost[(i, j)] * q[i][j] for i in C for j in F)
    ), "TotalCost"

    # (1) Satisfacción de demanda de cada cliente
    for i in C:
        mdl += pl.lpSum(q[i][j] for j in F) == demand[i], f"demand_{i}"

    # (2) Capacidad de cada almacén
    for j in F:
        mdl += pl.lpSum(q[i][j] for i in C) <= capacity[j] * y[j], f"capacity_{j}"

    # (3) Asignación sólo si y_j = 1  (vinculación con Big-M)
    #     Se usa capacidad como M natural del almacén
    for i in C:
        for j in F:
            mdl += q[i][j] <= capacity[j] * y[j], f"link_{i}_{j}"

    # (4) Límite de nº de almacenes abiertos (opcional)
    if isinstance(max_facilities, int) and max_facilities > 0:
        mdl += pl.lpSum(y[j] for j in F) <= max_facilities, "max_facilities"

    # (5) Radio máximo de servicio (opcional) – fuerza q_ij=0 si d_ij > radio
    if isinstance(max_service_km, (int, float)) and max_service_km > 0:
        for i in C:
            for j in F:
                if dist[(i, j)] > max_service_km:
                    mdl += q[i][j] == 0, f"radius_{i}_{j}"

    # Resolver
    opt = pl.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
    mdl.solve(opt)
    status = pl.LpStatus[mdl.status]

    # Resultados
    y_val = {j: int(round(y[j].value() or 0)) for j in F}
    q_rows = []
    for i in C:
        for j in F:
            val = q[i][j].value()
            if val is None:
                val = 0.0
            q_rows.append([i, j, float(val)])

    df_y = pd.DataFrame({"facility": list(y_val.keys()), "open": list(y_val.values())})
    df_q = pd.DataFrame(q_rows, columns=["customer", "facility", "qty_units"])

    # Costes
    fixed_sum = sum(fixed_cost[j] * y_val[j] for j in F)
    transp_sum = 0.0
    for _, row in df_q.iterrows():
        i, j, qty = row["customer"], row["facility"], row["qty_units"]
        transp_sum += transp_cost[(i, j)] * qty
    total_cost = fixed_sum + transp_sum

    # KPIs
    # Distancia media ponderada por demanda
    df_demand = cus[["id", "demand_units"]].rename(columns={"id": "customer"})
    df_tmp = df_q.merge(df_demand, on="customer", how="left")
    df_tmp = df_tmp.merge(
        pd.DataFrame(
            [{"customer": i, "facility": j, "dist_km": dist[(i, j)]} for i in C for j in F]
        ),
        on=["customer", "facility"], how="left"
    )
    # Cada i reparte su demanda en varios j; calculamos dist media ponderada por qty
    if df_tmp["qty_units"].sum() > 0:
        avg_dist = (df_tmp["dist_km"] * df_tmp["qty_units"]).sum() / df_tmp["qty_units"].sum()
    else:
        avg_dist = 0.0

    kpis = {
        "status": status,
        "total_cost": round(total_cost, 2),
        "fixed_cost": round(fixed_sum, 2),
        "transport_cost": round(transp_sum, 2),
        "open_facilities": int(df_y["open"].sum()),
        "avg_distance_km": round(avg_dist, 2),
        "demand_total": int(df_demand["demand_units"].sum()),
    }

    return SolveResult(
        status=status,
        total_cost=total_cost,
        fixed_cost=fixed_sum,
        transport_cost=transp_sum,
        open_facilities=df_y,
        assignment=df_q,
        kpis=kpis
    )


# -------------------- Export --------------------
def export_outputs(res: SolveResult, outdir: str):
    ensure_dir(outdir)

    # Filtra sólo asignaciones positivas para legibilidad
    assign_pos = res.assignment[res.assignment["qty_units"] > 1e-6].copy()
    assign_pos.sort_values(["facility", "customer"], inplace=True)

    res.open_facilities.to_csv(os.path.join(outdir, "facilities_open.csv"), index=False)
    assign_pos.to_csv(os.path.join(outdir, "assignment.csv"), index=False)

    with open(os.path.join(outdir, "kpi_summary.md"), "w", encoding="utf-8") as f:
        f.write("# Facility Location – KPI Summary\n\n")
        for k, v in res.kpis.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## Facilities abiertas\n")
        for _, r in res.open_facilities.iterrows():
            if int(r["open"]) == 1:
                f.write(f"- {r['facility']}\n")
        f.write("\n## Muestras de asignación (primeras 20 filas)\n")
        f.write(assign_pos.head(20).to_string(index=False))


# -------------------- CLI --------------------
def main():
    parser = argparse.ArgumentParser(description="Capacitated Facility Location (MILP)")
    parser.add_argument("--data-dir", default="data", help="Carpeta con facilities.csv y customers.csv")
    parser.add_argument("--outdir", default="outputs", help="Carpeta de salida")
    parser.add_argument("--cost-per-km-unit", type=float, default=0.35, help="€/unidad·km de transporte")
    parser.add_argument("--max-facilities", type=int, default=None, help="Límite de almacenes a abrir (opcional)")
    parser.add_argument("--max-service-km", type=float, default=None, help="Radio máximo de servicio en km (opcional)")
    parser.add_argument("--time-limit", type=int, default=120, help="Límite de tiempo del solver (s)")
    args = parser.parse_args()

    fac, cus = load_or_simulate(args.data_dir)
    res = build_and_solve(
        fac=fac,
        cus=cus,
        cost_per_km_unit=args.cost_per_km_unit,
        max_facilities=args.max_facilities,
        max_service_km=args.max_service_km,
        time_limit=args.time_limit
    )
    export_outputs(res, args.outdir)

    print("\n=== Resultado del modelo ===")
    print(f"Status: {res.kpis['status']}")
    print(f"Coste total: {res.kpis['total_cost']} (fijo {res.kpis['fixed_cost']} + transporte {res.kpis['transport_cost']})")
    print(f"Almacenes abiertos: {res.kpis['open_facilities']}")
    print(f"Distancia media ponderada (km): {res.kpis['avg_distance_km']}")
    print(f"Outputs en: {os.path.abspath(args.outdir)}")

if __name__ == "__main__":
    main()
