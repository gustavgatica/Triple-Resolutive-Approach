"""
TS-Básico para CVRP (Capacitated Vehicle Routing Problem)
==========================================================
Vecindario: relocate — mover un cliente de una ruta a otra posición
Lista tabú: fija, tamaño 10, almacena (customer_node, origin_route_idx)
Criterio de parada: max_iter iteraciones

Formato de instancia (loader.py):
  dist_matrix[i][j]: distancia entre nodos; nodo 0 = depósito, nodos 1..n = clientes
  customers: lista de tuplas (x, y, demand), índice i -> nodo i+1
  depot: tupla (x, y) para nodo 0
  capacity: capacidad de cada vehículo
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


DEPOT = 0  # depot is always node 0 in dist_matrix

# ---------------------------------------------------------------------------
# Route utilities
# ---------------------------------------------------------------------------

def _route_cost(route, dist):
    """Cost: depot -> r[0] -> ... -> r[-1] -> depot (node indices)."""
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


def _clarke_wright_init(n_customers, capacity, demands, dist):
    """
    Clarke-Wright savings heuristic.
    Customer nodes: 1 .. n_customers (depot = 0).
    """
    cust_ids = list(range(1, n_customers + 1))

    # Start: one route per customer
    routes = [[c] for c in cust_ids]

    # Compute savings
    savings = []
    for idx_a, a in enumerate(cust_ids):
        for b in cust_ids[idx_a + 1:]:
            s = dist[DEPOT][a] + dist[DEPOT][b] - dist[a][b]
            savings.append((s, a, b))
    savings.sort(reverse=True)

    def find_route_idx(routes, node):
        for i, r in enumerate(routes):
            if node in r:
                return i
        return None

    for _, a, b in savings:
        ra_idx = find_route_idx(routes, a)
        rb_idx = find_route_idx(routes, b)
        if ra_idx is None or rb_idx is None or ra_idx == rb_idx:
            continue
        ra, rb = routes[ra_idx], routes[rb_idx]
        if _route_load(ra, demands) + _route_load(rb, demands) > capacity:
            continue

        merged = None
        if ra[-1] == a and rb[0] == b:
            merged = (ra_idx, rb_idx, ra + rb)
        elif rb[-1] == a and ra[0] == b:
            merged = (rb_idx, ra_idx, rb + ra)
        elif ra[-1] == b and rb[0] == a:
            merged = (ra_idx, rb_idx, ra + rb[::-1])
        elif rb[-1] == b and ra[0] == a:
            merged = (rb_idx, ra_idx, rb + ra[::-1])

        if merged:
            i1, i2, new_route = merged
            routes[i1] = new_route
            routes.pop(i2)

    return routes


# ---------------------------------------------------------------------------
# Main solver
# ---------------------------------------------------------------------------

def solve(instance_data: dict,
          tabu_size: int = 10,
          max_iter: int = 1500,
          seed: int = 42) -> dict:
    """
    Tabu Search Básico para CVRP.

    Returns
    -------
    dict with keys:
        value     : best total route cost (float)
        solution  : list of routes (each = list of customer node indices)
        iterations: int
        time_s    : float
        history   : list of (iteration, best_value) tuples
    """
    random.seed(seed)

    capacity   = instance_data['capacity']
    n_cust     = instance_data['n_customers']
    customers  = instance_data['customers']   # list of (x, y, demand)
    dist       = instance_data['dist_matrix']

    # demands[node] = demand; nodes 1..n_cust
    demands = {i + 1: customers[i][2] for i in range(n_cust)}

    # --- Initial solution via Clarke-Wright ---
    routes = _clarke_wright_init(n_cust, capacity, demands, dist)

    def copy_routes(r):
        return [list(x) for x in r]

    cur_cost   = _total_cost(routes, dist)
    best_routes = copy_routes(routes)
    best_cost   = cur_cost

    tabu_list = deque(maxlen=tabu_size)
    history   = [(0, best_cost)]

    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):
        best_delta = float('inf')
        best_move  = None

        n_routes = len(routes)

        # --- Relocate neighborhood ---
        for ri in range(n_routes):
            for pos_rem, customer in enumerate(routes[ri]):
                for rj in range(n_routes):
                    if ri == rj:
                        continue
                    if _route_load(routes[rj], demands) + demands[customer] > capacity:
                        continue

                    r_ri = routes[ri]
                    before_rem = r_ri[pos_rem - 1] if pos_rem > 0 else DEPOT
                    after_rem  = r_ri[pos_rem + 1] if pos_rem < len(r_ri) - 1 else DEPOT
                    remove_gain = (dist[before_rem][customer] +
                                   dist[customer][after_rem] -
                                   dist[before_rem][after_rem])

                    r_rj = routes[rj]
                    for ins_pos in range(len(r_rj) + 1):
                        before_ins = r_rj[ins_pos - 1] if ins_pos > 0 else DEPOT
                        after_ins  = r_rj[ins_pos]     if ins_pos < len(r_rj) else DEPOT
                        insert_cost = (dist[before_ins][customer] +
                                       dist[customer][after_ins] -
                                       dist[before_ins][after_ins])

                        delta    = insert_cost - remove_gain
                        move_key = (customer, ri)
                        is_tabu  = move_key in tabu_list
                        new_cost = cur_cost + delta

                        if is_tabu and new_cost >= best_cost:
                            continue

                        if delta < best_delta:
                            best_delta = delta
                            best_move  = (customer, ri, pos_rem, rj, ins_pos, move_key)

        if best_move is None:
            history.append((it, best_cost))
            continue

        customer, ri, pos_rem, rj, ins_pos, tabu_key = best_move

        routes[ri].pop(pos_rem)
        routes[rj].insert(ins_pos, customer)
        routes = [r for r in routes if r]

        cur_cost += best_delta
        tabu_list.append(tabu_key)

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


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    instances = list_all_instances(
        os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    vrp_files = instances.get('vrp', [])

    if not vrp_files:
        print("No VRP instances found.")
        sys.exit(1)

    print(f"{'Instance':<12} {'BKS':>8} {'TS-Básico':>10} {'GAP%':>8} {'Routes':>7} {'Time(s)':>8}")
    print('-' * 60)
    for fp in vrp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10.1f} {gap:>7.2f}% "
              f"{len(res['solution']):>7} {res['time_s']:>8.4f}")
