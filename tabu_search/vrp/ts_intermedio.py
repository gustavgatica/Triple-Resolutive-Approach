"""
TS-Intermedio para CVRP
========================
Mejoras sobre TS-Básico:
  1. Lista tabú DINÁMICA [7, 20].
  2. Criterio de ASPIRACIÓN explícito (acepta tabú si mejora el best global).
  3. Vecindario AMPLIADO: relocate + 2-opt intra-ruta.
  4. Mayor número de iteraciones (3000 vs 1500).

Nodo 0 = depósito; nodos 1..n = clientes (indexación de dist_matrix).
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances

DEPOT = 0


# ---------------------------------------------------------------------------
# Utilidades de ruta
# ---------------------------------------------------------------------------

def _route_cost(route, dist):
    if not route:
        return 0.0
    c = dist[DEPOT][route[0]]
    for i in range(len(route) - 1):
        c += dist[route[i]][route[i + 1]]
    c += dist[route[-1]][DEPOT]
    return c


def _total_cost(routes, dist):
    return sum(_route_cost(r, dist) for r in routes)


def _route_load(route, demands):
    return sum(demands[c] for c in route)


def _clarke_wright_init(n_cust, capacity, demands, dist):
    cust_ids = list(range(1, n_cust + 1))
    routes   = [[c] for c in cust_ids]

    savings = []
    for idx_a, a in enumerate(cust_ids):
        for b in cust_ids[idx_a + 1:]:
            savings.append((dist[DEPOT][a] + dist[DEPOT][b] - dist[a][b], a, b))
    savings.sort(reverse=True)

    def find_idx(routes, node):
        for i, r in enumerate(routes):
            if node in r:
                return i
        return None

    for _, a, b in savings:
        ra, rb = find_idx(routes, a), find_idx(routes, b)
        if ra is None or rb is None or ra == rb:
            continue
        if _route_load(routes[ra], demands) + _route_load(routes[rb], demands) > capacity:
            continue
        ra_r, rb_r = routes[ra], routes[rb]
        merged = None
        if ra_r[-1] == a and rb_r[0] == b:
            merged = (ra, rb, ra_r + rb_r)
        elif rb_r[-1] == a and ra_r[0] == b:
            merged = (rb, ra, rb_r + ra_r)
        elif ra_r[-1] == b and rb_r[0] == a:
            merged = (ra, rb, ra_r + rb_r[::-1])
        elif rb_r[-1] == b and ra_r[0] == a:
            merged = (rb, ra, rb_r + ra_r[::-1])
        if merged:
            i1, i2, nr = merged
            routes[i1] = nr
            routes.pop(i2)
    return routes


# ---------------------------------------------------------------------------
# Movimientos de vecindario
# ---------------------------------------------------------------------------

def _relocate_moves(routes, demands, capacity, dist):
    """Generador de movimientos relocate con su delta de coste."""
    n_routes = len(routes)
    for ri in range(n_routes):
        for pos_rem, customer in enumerate(routes[ri]):
            r_ri = routes[ri]
            before_rem = r_ri[pos_rem - 1] if pos_rem > 0 else DEPOT
            after_rem  = r_ri[pos_rem + 1] if pos_rem < len(r_ri) - 1 else DEPOT
            remove_gain = (dist[before_rem][customer] + dist[customer][after_rem]
                           - dist[before_rem][after_rem])

            for rj in range(n_routes):
                if ri == rj:
                    continue
                if _route_load(routes[rj], demands) + demands[customer] > capacity:
                    continue
                r_rj = routes[rj]
                for ins_pos in range(len(r_rj) + 1):
                    b_ins = r_rj[ins_pos - 1] if ins_pos > 0 else DEPOT
                    a_ins = r_rj[ins_pos]     if ins_pos < len(r_rj) else DEPOT
                    insert_cost = (dist[b_ins][customer] + dist[customer][a_ins]
                                   - dist[b_ins][a_ins])
                    delta    = insert_cost - remove_gain
                    move_key = (customer, ri)
                    yield delta, move_key, (customer, ri, pos_rem, rj, ins_pos)


def _intra_two_opt(routes, dist):
    """Generador de movimientos 2-opt dentro de cada ruta.
    Nodo 0 = depósito; al cruzar el límite de la ruta se usa el depósito.
    """
    for ri, route in enumerate(routes):
        n = len(route)
        if n < 4:
            continue
        for i in range(n - 1):
            for j in range(i + 2, n):
                a = route[i]
                b = route[i + 1]                      # siempre válido pues i < n-1
                c = route[j]
                d = route[j + 1] if j + 1 < n else DEPOT   # depósito al final
                delta    = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                move_key = (min(route[i], route[j]), max(route[i], route[j]))
                yield delta, move_key, (ri, i, j)


# ---------------------------------------------------------------------------
# Solver principal
# ---------------------------------------------------------------------------

def solve(instance_data: dict,
          tabu_min: int = 7,
          tabu_max: int = 20,
          change_every: int = 150,
          max_iter: int = 3000,
          seed: int = 42) -> dict:
    """
    Tabu Search Intermedio para CVRP.

    Returns dict: value, solution, iterations, time_s, history
    """
    random.seed(seed)

    capacity = instance_data['capacity']
    n_cust   = instance_data['n_customers']
    customers = instance_data['customers']
    dist     = instance_data['dist_matrix']
    demands  = {i + 1: customers[i][2] for i in range(n_cust)}

    routes   = _clarke_wright_init(n_cust, capacity, demands, dist)

    def copy_routes(r):
        return [list(x) for x in r]

    cur_cost    = _total_cost(routes, dist)
    best_routes = copy_routes(routes)
    best_cost   = cur_cost

    tabu_size = random.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    history = [(0, best_cost)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = random.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        best_delta = float('inf')
        best_move  = None
        best_type  = None

        # --- Relocate neighborhood ---
        for delta, move_key, move_data in _relocate_moves(routes, demands, capacity, dist):
            is_tabu  = move_key in tabu_list
            new_cost = cur_cost + delta
            if is_tabu and new_cost >= best_cost:
                continue
            if delta < best_delta:
                best_delta = delta
                best_move  = (move_key, move_data)
                best_type  = 'relocate'

        # --- Intra-route 2-opt neighborhood ---
        for delta, move_key, move_data in _intra_two_opt(routes, dist):
            is_tabu  = move_key in tabu_list
            new_cost = cur_cost + delta
            if is_tabu and new_cost >= best_cost:
                continue
            if delta < best_delta:
                best_delta = delta
                best_move  = (move_key, move_data)
                best_type  = '2opt'

        if best_move is None:
            history.append((it, best_cost))
            continue

        move_key, move_data = best_move

        # Apply move
        if best_type == 'relocate':
            customer, ri, pos_rem, rj, ins_pos = move_data
            routes[ri].pop(pos_rem)
            routes[rj].insert(ins_pos, customer)
            routes = [r for r in routes if r]
        else:  # 2opt
            ri, i, j = move_data
            routes[ri][i + 1:j + 1] = routes[ri][i + 1:j + 1][::-1]

        cur_cost += best_delta
        tabu_list.append(move_key)

        if cur_cost < best_cost:
            best_routes = copy_routes(routes)
            best_cost   = cur_cost

        history.append((it, best_cost))

    elapsed = time.perf_counter() - t0
    return {
        'value':      best_cost,
        'solution':   best_routes,
        'iterations': it,
        'time_s':     elapsed,
        'history':    history,
    }


if __name__ == '__main__':
    instances = list_all_instances(
        os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    vrp_files = instances.get('vrp', [])
    print(f"{'Instance':<12} {'BKS':>8} {'TS-Inter':>10} {'GAP%':>8} {'Routes':>7} {'Time(s)':>8}")
    print('-' * 60)
    for fp in vrp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10.1f} {gap:>7.2f}% "
              f"{len(res['solution']):>7} {res['time_s']:>8.4f}")
