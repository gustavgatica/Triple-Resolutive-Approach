"""
knapsack_dp.py — Solver exacto para el Problema de la Mochila 0-1
mediante Programación Dinámica (DP).

Complejidad:  O(n · W)  en tiempo,  O(W)  en espacio (optimización 1D).

Uso desde línea de comandos:
    python knapsack_dp.py ../../instances/knapsack/knapPI_11.kp

Uso como módulo:
    from knapsack_dp import solve_knapsack
    result = solve_knapsack(profits, weights, capacity)
"""

import sys
import os
import time

# ── Asegurar acceso al loader ──────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_knapsack


def solve_knapsack(profits: list, weights: list, capacity: int) -> dict:
    """
    Resuelve el Knapsack 0-1 con DP exacto.

    Parámetros:
        profits  : lista de beneficios [p_1, ..., p_n]
        weights  : lista de pesos      [w_1, ..., w_n]
        capacity : capacidad máxima W

    Retorna:
        dict con:
            'value'    : valor óptimo (int)
            'selected' : lista booleana de artículos seleccionados
            'weight'   : peso total de la solución
    """
    n = len(profits)
    # Tabla DP 1D (ahorro de memoria)
    dp = [0] * (capacity + 1)

    # Fase de llenado (backward para evitar reuso en la misma iteración)
    for i in range(n):
        wi, pi = weights[i], profits[i]
        for w in range(capacity, wi - 1, -1):
            if dp[w - wi] + pi > dp[w]:
                dp[w] = dp[w - wi] + pi

    optimal_value = dp[capacity]

    # Reconstrucción de la solución (traceback)
    selected = [False] * n
    w_rem = capacity
    for i in range(n - 1, -1, -1):
        wi, pi = weights[i], profits[i]
        if w_rem >= wi and dp[w_rem] == dp[w_rem - wi] + pi:
            selected[i] = True
            w_rem -= wi

    total_weight = sum(weights[i] for i in range(n) if selected[i])

    return {
        'value':    optimal_value,
        'selected': selected,
        'weight':   total_weight,
    }


def solve_from_file(filepath: str) -> dict:
    """Carga una instancia .kp y la resuelve."""
    inst = load_knapsack(filepath)
    t0 = time.perf_counter()
    result = solve_knapsack(inst['profits'], inst['weights'], inst['capacity'])
    elapsed = time.perf_counter() - t0

    gap = None
    if inst['bks'] is not None:
        gap = abs(inst['bks'] - result['value']) / inst['bks'] * 100.0

    return {
        'instance':  inst['name'],
        'n':         inst['n'],
        'capacity':  inst['capacity'],
        'bks':       inst['bks'],
        'value':     result['value'],
        'weight':    result['weight'],
        'gap_pct':   gap,
        'time_s':    elapsed,
        'selected':  result['selected'],
    }


def print_result(r: dict):
    print(f"\nInstancia : {r['instance']}")
    print(f"n         : {r['n']} artículos")
    print(f"Capacidad : {r['capacity']}")
    print(f"BKS       : {r['bks']}")
    print(f"Valor DP  : {r['value']}")
    print(f"Peso usado: {r['weight']}")
    if r['gap_pct'] is not None:
        print(f"GAP       : {r['gap_pct']:.4f}%")
    print(f"Tiempo    : {r['time_s']:.4f} s")
    n_sel = sum(r['selected'])
    print(f"Artículos seleccionados: {n_sel}/{r['n']}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python knapsack_dp.py <archivo.kp>")
        print("\nEjecutando en TODAS las instancias del proyecto...")

        base = os.path.join(os.path.dirname(__file__), '..', '..', 'instances', 'knapsack')
        files = sorted(f for f in os.listdir(base) if f.endswith('.kp'))
        if not files:
            print("  No se encontraron archivos .kp")
            sys.exit(1)

        print(f"\n{'Instancia':<15} {'BKS':>8} {'DP':>8} {'GAP%':>8} {'Tiempo(s)':>10}")
        print("-" * 55)
        for fname in files:
            r = solve_from_file(os.path.join(base, fname))
            gap_str = f"{r['gap_pct']:.4f}" if r['gap_pct'] is not None else "N/A"
            print(f"{r['instance']:<15} {str(r['bks']):>8} {r['value']:>8} {gap_str:>8} {r['time_s']:>10.4f}")
    else:
        r = solve_from_file(sys.argv[1])
        print_result(r)
