"""
metrics.py — Cálculo de métricas de rendimiento para los experimentos.

Funciones:
  gap(value, bks, minimization)  → GAP% respecto al BKS
  summarize(result, bks, minimization) → dict con todas las métricas
"""

from __future__ import annotations


def gap(value: float, bks: float, minimization: bool = True) -> float:
    """
    Calcula el GAP porcentual respecto al Best Known Solution (BKS).

    Minimización (TSP, VRP, Flowshop, Job Shop):
        GAP = (value - BKS) / BKS * 100
    Maximización (Knapsack):
        GAP = (BKS - value) / BKS * 100

    Un GAP negativo indica que se superó el BKS (posible en instancias
    donde el BKS fue estimado empíricamente).
    """
    if bks <= 0:
        return 0.0
    if minimization:
        return (value - bks) / bks * 100.0
    else:
        return (bks - value) / bks * 100.0


# Indica si el problema es de minimización
MINIMIZATION: dict[str, bool] = {
    "knapsack": False,   # maximizar valor
    "tsp":      True,
    "vrp":      True,
    "flowshop": True,
    "jobshop":  True,
}


def summarize(result: dict, instance_data: dict, problema: str) -> dict:
    """
    Construye un diccionario de métricas a partir del resultado del solver.

    Parameters
    ----------
    result        : dict devuelto por solve()
    instance_data : dict devuelto por load_instance()
    problema      : 'knapsack' | 'tsp' | 'vrp' | 'flowshop' | 'jobshop'

    Returns
    -------
    dict con:
        value, bks, gap_pct, iterations, time_s, is_minimization
    """
    minimization = MINIMIZATION.get(problema, True)
    bks          = instance_data.get('bks', result['value'])
    value        = result['value']

    return {
        'value':          value,
        'bks':            bks,
        'gap_pct':        gap(value, bks, minimization),
        'iterations':     result.get('iterations', 0),
        'time_s':         result.get('time_s', 0.0),
        'is_minimization': minimization,
    }
