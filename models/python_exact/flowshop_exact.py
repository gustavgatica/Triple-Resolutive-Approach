"""
flowshop_exact.py — Solver exacto para Permutation Flowshop (n pequeño)
mediante búsqueda exhaustiva con poda + heurística NEH como referencia.

- Para n ≤ 10: búsqueda exhaustiva (n! permutaciones).
- Para n > 10: solo heurística NEH (cota inferior de calidad).

Uso:
    python flowshop_exact.py ../../instances/flowshop/ta001.fsp
"""

import sys, os, time
from itertools import permutations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_flowshop


def makespan(perm: list, p: list, n_machines: int) -> int:
    """
    Calcula el Makespan de una permutación de trabajos.
    perm: lista de índices de trabajos (0-based)
    p   : matriz de tiempos p[job][machine]
    """
    n = len(perm)
    C = [[0] * n_machines for _ in range(n)]
    for i, job in enumerate(perm):
        for j in range(n_machines):
            prev_job  = C[i - 1][j]     if i > 0 else 0
            prev_mach = C[i][j - 1]     if j > 0 else 0
            C[i][j] = max(prev_job, prev_mach) + p[job][j]
    return C[n - 1][n_machines - 1]


def neh_heuristic(p: list, n_jobs: int, n_machines: int) -> tuple:
    """
    Heurística NEH (Nawaz-Enscore-Ham, 1983).
    Construye una buena permutación de forma greedy.
    Retorna (makespan, permutación).
    """
    # Ordenar trabajos por suma total de tiempos (descendente)
    totals = [(sum(p[i]), i) for i in range(n_jobs)]
    totals.sort(reverse=True)
    order = [idx for _, idx in totals]

    perm = [order[0]]
    for k in range(1, n_jobs):
        job = order[k]
        best_ms, best_pos = float('inf'), 0
        for pos in range(len(perm) + 1):
            candidate = perm[:pos] + [job] + perm[pos:]
            ms = makespan(candidate, p, n_machines)
            if ms < best_ms:
                best_ms, best_pos = ms, pos
        perm = perm[:best_pos] + [job] + perm[best_pos:]

    return makespan(perm, p, n_machines), perm


def exhaustive_search(p: list, n_jobs: int, n_machines: int) -> tuple:
    """Búsqueda exhaustiva. Solo para n ≤ 10."""
    best_ms, best_perm = float('inf'), None
    for perm in permutations(range(n_jobs)):
        ms = makespan(list(perm), p, n_machines)
        if ms < best_ms:
            best_ms, best_perm = ms, list(perm)
    return best_ms, best_perm


def solve_from_file(filepath: str) -> dict:
    inst = load_flowshop(filepath)
    n, m = inst['n_jobs'], inst['n_machines']
    p = inst['processing']
    bks = inst['bks']

    t0 = time.perf_counter()
    if n <= 10:
        value, perm = exhaustive_search(p, n, m)
        method = 'Exacto (exhaustivo)'
    else:
        value, perm = neh_heuristic(p, n, m)
        method = f'NEH (heurística, n={n})'
    elapsed = time.perf_counter() - t0

    gap = (value - bks) / bks * 100.0 if bks else None

    return {
        'instance': inst['name'],
        'n_jobs': n, 'n_machines': m,
        'bks': bks, 'value': value,
        'perm': perm, 'method': method,
        'gap_pct': gap, 'time_s': elapsed,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        base = os.path.join(os.path.dirname(__file__), '..', '..', 'instances', 'flowshop')
        files = sorted(f for f in os.listdir(base) if f.endswith('.fsp'))
        print(f"\n{'Instancia':<10} {'n×m':>8} {'BKS':>8} {'Valor':>8} {'GAP%':>8} {'Tiempo(s)':>10}  Método")
        print("-" * 70)
        for fname in files:
            r = solve_from_file(os.path.join(base, fname))
            gap_str = f"{r['gap_pct']:.2f}" if r['gap_pct'] is not None else "N/A"
            nm = f"{r['n_jobs']}×{r['n_machines']}"
            print(f"{r['instance']:<10} {nm:>8} {str(r['bks']):>8} {r['value']:>8} "
                  f"{gap_str:>8} {r['time_s']:>10.4f}  {r['method']}")
    else:
        r = solve_from_file(sys.argv[1])
        print(f"{r['instance']}: {r['method']} → {r['value']} (BKS={r['bks']}, GAP={r['gap_pct']:.2f}%)")
