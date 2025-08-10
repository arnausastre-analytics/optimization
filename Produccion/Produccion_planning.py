# scripts/production_planning.py
# ==============================================================
# Optimización de producción con restricciones de capacidad
# y costes energéticos por turno (MILP con PuLP).
# --------------------------------------------------------------
# Entradas opcionales (CSV en ./data):
#  - products.csv:
#      product,price_per_unit,min_demand,max_demand
#  - machines.csv:
#      machine,shift,available_hours
#  - routings.csv:
#      product,machine,proc_time_per_unit_min,energy_kwh_per_unit,setup_time_min,setup_cost
#  - energy.csv:
#      shift,energy_price_eur_kwh
#
# Si no existen, se generan datos SIMULADOS reproducibles.
#
# Salidas (./outputs):
#  - production_plan.csv   -> asignación x[p,m,s] y binarios y[p,m,s]
#  - shift_utilization.csv -> utilización por máquina/turno
#  - kpi_summary.md        -> métricas y resultado económico
# ==============================================================

import os
import sys
import argparse
import random
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

try:
    import pulp as pl
except ImportError:
    print("Instalando PuLP...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pulp"])
    import pulp as pl

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


# ---------- Utilidades de E/S ----------
def ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_or_simulate_data(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lee CSVs si existen; si no, crea datos simulados realistas."""
    ensure_dirs(data_dir)

    p_path = os.path.join(data_dir, "products.csv")
    m_path = os.path.join(data_dir, "machines.csv")
    r_path = os.path.join(data_dir, "routings.csv")
    e_path = os.path.join(data_dir, "energy.csv")

    if all(os.path.exists(p) for p in [p_path, m_path, r_path, e_path]):
        products = pd.read_csv(p_path)
        machines = pd.read_csv(m_path)
        routings = pd.read_csv(r_path)
        energy = pd.read_csv(e_path)
        return products, machines, routings, energy

    # --- Simulación ---
    print("[i] No se encontraron CSVs. Generando dataset simulado en ./data ...")

    products = pd.DataFrame({
        "product": ["P1", "P2", "P3", "P4"],
        "price_per_unit": [22.0, 35.0, 28.0, 31.0],
        "min_demand": [200, 120, 160, 90],
        "max_demand": [480, 300, 420, 240],
    })

    machines = pd.DataFrame({
        "machine": ["M1", "M1", "M2", "M2", "M3", "M3"],
        "shift":   ["S1", "S2", "S1", "S2", "S1", "S2"],
        "available_hours": [7.5, 7.5, 7.5, 7.5, 7.5, 7.5],  # jornada útil por turno
    })

    # Ruteo / parámetros tecnológicos por (producto, máquina)
    rows = []
    for p in products["product"]:
        for m in ["M1", "M2", "M3"]:
            # no todas las combinaciones son válidas
            if (p in ["P1", "P2"] and m == "M3") or (p in ["P3", "P4"] and m == "M1"):
                continue
            proc = np.random.uniform(2.5, 6.0)  # minutos por unidad
            energy = np.random.uniform(0.08, 0.18)  # kWh por unidad
            setup_t = np.random.uniform(15, 45)     # min
            setup_c = np.random.uniform(25, 80)     # €
            rows.append([p, m, round(proc, 2), round(energy, 3), round(setup_t, 1), round(setup_c, 2)])
    routings = pd.DataFrame(rows, columns=[
        "product", "machine", "proc_time_per_unit_min", "energy_kwh_per_unit", "setup_time_min", "setup_cost"
    ])

    energy = pd.DataFrame({
        "shift": ["S1", "S2"],
        "energy_price_eur_kwh": [0.14, 0.22]  # pico/valle inverso
    })

    products.to_csv(p_path, index=False)
    machines.to_csv(m_path, index=False)
    routings.to_csv(r_path, index=False)
    energy.to_csv(e_path, index=False)

    print("[i] Dataset simulado guardado en ./data")
    return products, machines, routings, energy


# ---------- Modelo MILP ----------
@dataclass
class ModelResult:
    status: str
    obj_value: float
    x: pd.DataFrame
    y: pd.DataFrame
    util: pd.DataFrame
    kpis: Dict[str, float]


def build_and_solve(products: pd.DataFrame,
                    machines: pd.DataFrame,
                    routings: pd.DataFrame,
                    energy: pd.DataFrame,
                    solver: str = "PULP_CBC_CMD",
                    time_limit: int = 60) -> ModelResult:
    """
    Variables:
      x[p,m,s]  >= 0  -> Unidades de producto p en máquina m, turno s
      y[p,m,s] in {0,1} -> 1 si se produce p en (m,s) (activa setup y tiempo de cambio)
    """

    # Sets
    P = products["product"].unique().tolist()
    M = machines["machine"].unique().tolist()
    S = machines["shift"].unique().tolist()

    # Parámetros
    price = products.set_index("product")["price_per_unit"].to_dict()
    dmin = products.set_index("product")["min_demand"].to_dict()
    dmax = products.set_index("product")["max_demand"].to_dict()

    # map (p,m)-> tech params
    tech = routings.set_index(["product", "machine"]).to_dict(orient="index")
    # precio de energía por turno
    eprice = energy.set_index("shift")["energy_price_eur_kwh"].to_dict()
    # horas disponibles por (m,s)
    hours = machines.set_index(["machine", "shift"])["available_hours"].to_dict()

    # Model
    mdl = pl.LpProblem("ProductionPlanning_EnergyAware", pl.LpMaximize)

    # Variables
    X = pl.LpVariable.dicts("x", (P, M, S), lowBound=0, cat=pl.LpContinuous)
    Y = pl.LpVariable.dicts("y", (P, M, S), lowBound=0, upBound=1, cat=pl.LpBinary)

    # Objetivo = Ingresos - Coste Energético - Coste Setup
    revenue = pl.lpSum(price[p] * X[p][m][s]
                       for p in P for m in M for s in S
                       if (p, m) in tech)

    energy_cost = pl.lpSum(
        eprice[s] * tech[(p, m)]["energy_kwh_per_unit"] * X[p][m][s]
        for p in P for m in M for s in S
        if (p, m) in tech
    )

    setup_cost = pl.lpSum(
        tech[(p, m)]["setup_cost"] * Y[p][m][s]
        for p in P for m in M for s in S
        if (p, m) in tech
    )

    mdl += revenue - energy_cost - setup_cost, "Profit"

    # 1) Demanda mínima y máxima por producto
    for p in P:
        mdl += pl.lpSum(X[p][m][s] for m in M for s in S if (p, m) in tech) >= dmin[p], f"min_demand_{p}"
        mdl += pl.lpSum(X[p][m][s] for m in M for s in S if (p, m) in tech) <= dmax[p], f"max_demand_{p}"

    # 2) Capacidad por máquina/turno (tiempo de proceso + setup)
    for m in M:
        for s in S:
            mdl += pl.lpSum(
                tech[(p, m)]["proc_time_per_unit_min"] * X[p][m][s] +
                tech[(p, m)]["setup_time_min"] * Y[p][m][s]
                for p in P if (p, m) in tech
            ) <= hours[(m, s)] * 60.0, f"capacity_{m}_{s}"

    # 3) Enlazar X con Y (si no activas Y, X debe ser 0)
    #    Big-M: limitar producción máxima razonable por slot (capacidad / tiempo unitario)
    for p in P:
        for m in M:
            if (p, m) not in tech:
                # inexistente: fuerza X=Y=0
                for s in S:
                    mdl += X[p][m][s] == 0
                    mdl += Y[p][m][s] == 0
                continue
            t_unit = tech[(p, m)]["proc_time_per_unit_min"]
            for s in S:
                M_big = (hours[(m, s)] * 60.0) / max(1e-6, t_unit)
                mdl += X[p][m][s] <= M_big * Y[p][m][s], f"link_{p}_{m}_{s}"

    # 4) (Opcional) Nº máximo de productos distintos por máquina/turno
    #    Evita planificaciones con demasiadas micro-lotes
    MAX_SKU_PER_SLOT = 3
    for m in M:
        for s in S:
            mdl += pl.lpSum(Y[p][m][s] for p in P if (p, m) in tech) <= MAX_SKU_PER_SLOT, f"limit_skus_{m}_{s}"

    # Solver
    if solver.upper() == "PULP_CBC_CMD":
        opt = pl.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
    else:
        opt = pl.PULP_CBC_CMD(msg=False, timeLimit=time_limit)  # default

    mdl.solve(opt)

    status = pl.LpStatus[mdl.status]
    obj = pl.value(mdl.objective)

    # Resultados detallados
    rows_x, rows_y = [], []
    for p in P:
        for m in M:
            for s in S:
                if (p, m) in tech:
                    xv = X[p][m][s].value()
                    yv = Y[p][m][s].value()
                    if (xv is None) or (yv is None):
                        xv, yv = 0.0, 0.0
                    rows_x.append([p, m, s, round(float(xv), 4)])
                    rows_y.append([p, m, s, int(round(float(yv)))])
    df_x = pd.DataFrame(rows_x, columns=["product", "machine", "shift", "qty"])
    df_y = pd.DataFrame(rows_y, columns=["product", "machine", "shift", "active"])

    # Utilización por slot (min usados / disponibles)
    util_rows = []
    for m in M:
        for s in S:
            used = 0.0
            for p in P:
                if (p, m) not in tech:
                    continue
                used += tech[(p, m)]["proc_time_per_unit_min"] * float(X[p][m][s].value() or 0.0)
                used += tech[(p, m)]["setup_time_min"] * float(Y[p][m][s].value() or 0.0)
            avail = hours[(m, s)] * 60.0
            util_rows.append([m, s, used, avail, used / avail if avail > 0 else 0.0])
    df_util = pd.DataFrame(util_rows, columns=["machine", "shift", "minutes_used", "minutes_avail", "utilization"])

    # KPIs
    df_merge = df_x.merge(df_y, on=["product", "machine", "shift"])
    df_merge = df_merge[df_merge["qty"] > 0]
    # Costes e ingresos desagregados
    def line_revenue(row):
        return price[row["product"]] * row["qty"]

    def line_energy(row):
        ep = eprice[row["shift"]]
        te = tech[(row["product"], row["machine"])]["energy_kwh_per_unit"]
        return ep * te * row["qty"]

    def line_setup(row):
        if row["active"] <= 0:
            return 0.0
        return tech[(row["product"], row["machine"])]["setup_cost"]

    df_merge["revenue"] = df_merge.apply(line_revenue, axis=1)
    df_merge["energy_cost"] = df_merge.apply(line_energy, axis=1)
    df_merge["setup_cost"] = df_merge.apply(line_setup, axis=1)

    KPIs = {
        "status": status,
        "objective_profit": round(float(obj or 0.0), 2),
        "total_qty": round(df_x["qty"].sum(), 2),
        "total_revenue": round(df_merge["revenue"].sum(), 2),
        "total_energy_cost": round(df_merge["energy_cost"].sum(), 2),
        "total_setup_cost": round(df_merge["setup_cost"].sum(), 2),
        "avg_utilization": round(df_util["utilization"].mean(), 3),
    }

    return ModelResult(status=status, obj_value=obj or 0.0,
                       x=df_x, y=df_y, util=df_util, kpis=KPIs)


# ---------- Export ----------
def export_results(res: ModelResult, outdir: str) -> None:
    ensure_dirs(outdir)
    plan = res.x.merge(res.y, on=["product", "machine", "shift"])
    plan = plan.sort_values(["machine", "shift", "qty"], ascending=[True, True, False])
    plan.to_csv(os.path.join(outdir, "production_plan.csv"), index=False)
    res.util.to_csv(os.path.join(outdir, "shift_utilization.csv"), index=False)

    with open(os.path.join(outdir, "kpi_summary.md"), "w", encoding="utf-8") as f:
        f.write("# Production Planning – KPI Summary\n\n")
        for k, v in res.kpis.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## Top lines (qty>0)\n")
        top = plan[plan["qty"] > 0].head(20)
        if len(top) > 0:
            for _, r in top.iterrows():
                f.write(f"- {r['product']} @ {r['machine']} {r['shift']} → {r['qty']}\n")


# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Production planning optimization (MILP)")
    parser.add_argument("--data-dir", default="data", help="Carpeta de entrada con CSVs (opcional)")
    parser.add_argument("--outdir", default="outputs", help="Carpeta de salida")
    parser.add_argument("--time-limit", type=int, default=60, help="Time limit solver (s)")
    args = parser.parse_args()

    products, machines, routings, energy = load_or_simulate_data(args.data_dir)
    res = build_and_solve(products, machines, routings, energy, time_limit=args.time_limit)
    export_results(res, args.outdir)

    print("\n=== Resultado del modelo ===")
    print(f"Status: {res.status}")
    print(f"Beneficio óptimo: {res.kpis['objective_profit']}")
    print(f"Utilización media: {res.kpis['avg_utilization']}")
    print(f"Outputs en: {os.path.abspath(args.outdir)}")

if __name__ == "__main__":
    main()
