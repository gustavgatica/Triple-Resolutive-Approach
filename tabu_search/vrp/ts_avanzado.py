"""
TS-Avanzado para CVRP
======================
Mejoras sobre TS-Intermedio:
  1. MEMORIA DE FRECUENCIA: freq[customer][route_size_bucket] registra con qué
     frecuencia un cliente fue reubicado. Penaliza clientes muy movidos.
  2. PENALIZACIÓN ADAPTATIVA λ: aumenta al estancarse, baja al mejorar.
  3. Vecindario COMPLETO: relocate + 2-opt intra-ruta + 2-opt inter-ruta (swap).
  4. DIVERSIFICACIÓN: al activarse, fuerza mover clientes con alta frecuencia.
  5. Más iteraciones (5000 en experimentos; CLI usa 2000).

Nodo 0 = depósito; nodos 1..n = clientes.
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
# Utilidades
# ---------------------------------------------------------------------------

def _route_cost(route, dist):
    if not route:
        return 0.0
    c = dist[DEPOT][route[0]]
    for k in range(len(route) - 1):
        c += dist[route[k]][route[k + 1]]
    c += dist[route[-1]][DEPOT]
    return c


def _total_cost(routes, dist):
    return sum(_route_cost(r, dist) for r in routes)


def _route_load(route, demands):
    return sum(demands[c] for c in route)


def _clarke_wright_init(n_cust, capacity, demands, dist):
    cust_ids = list(range(1, n_cust + 1))
    routes   = [[c] for c in cust_ids]
    savings  = []
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
# Generadores de vecindario
# ---------------------------------------------------------------------------

def _relocate_moves(routes, demands, capacity, dist, freq, lam):
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
                    delta     = insert_cost - remove_gain
                    move_key  = (customer, ri)
                    # Penalized delta: penalize frequently-moved customers
                    pen_delta = delta + lam * freq.get(customer, 0)
                    yield pen_delta, delta, move_key, ('relocate', customer, ri, pos_rem, rj, ins_pos)


def _intra_two_opt(routes, dist):
    for ri, route in enumerate(routes):
        n = len(route)
        if n < 4:
            continue
        for i in range(n - 1):
            for j in range(i + 2, n):
                a = route[i]; b = route[i + 1]
                c = route[j]; d = route[j + 1] if j + 1 < n else DEPOT
                delta    = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                move_key = (min(route[i], route[j]), max(route[i], route[j]))
                yield delta, delta, move_key, ('2opt_intra', ri, i, j)


def _inter_swap_moves(routes, demands, capacity, dist):
    """Swap a customer from route ri with one from route rj."""
    n_routes = len(routes)
    for ri in range(n_routes - 1):
        for rj in range(ri + 1, n_routes):
            for pi, ci in enumerate(routes[ri]):
                for pj, cj in enumerate(routes[rj]):
                    # Check capacity after swap
                    load_ri_new = _route_load(routes[ri], demands) - demands[ci] + demands[cj]
                    load_rj_new = _route_load(routes[rj], demands) - demands[cj] + demands[ci]
                    if load_ri_new > capacity or load_rj_new > capacity:
                        continue
                    # Delta for ri: remove ci at pi, insert cj at pi
                    r_ri = routes[ri]
                    b_ri = r_ri[pi - 1] if pi > 0 else DEPOT
                    a_ri = r_ri[pi + 1] if pi < len(r_ri) - 1 else DEPOT
                    delta_ri = (dist[b_ri][cj] + dist[cj][a_ri]
                                - dist[b_ri][ci] - dist[ci][a_ri])
                    # Delta for rj: remove cj at pj, insert ci at pj
                    r_rj = routes[rj]
                    b_rj = r_rj[pj - 1] if pj > 0 else DEPOT
                    a_rj = r_rj[pj + 1] if pj < len(r_rj) - 1 else DEPOT
                    delta_rj = (dist[b_rj][ci] + dist[ci][a_rj]
                                - dist[b_rj][cj] - dist[cj][a_rj])
                    delta    = delta_ri + delta_rj
                    move_key = (min(ci, cj), max(ci, cj))
                    yield delta, delta, move_key, ('swap_inter', ri, pi, ci, rj, pj, cj)


# ---------------------------------------------------------------------------
# Solver principal
# ---------------------------------------------------------------------------

def solve(instance_data: dict,
          tabu_min: int = 7,
          tabu_max: int = 25,
          change_every: int = 200,
          lambda_init: float = 0.0,
          lambda_max: float = 3.0,
          lambda_step_up: float = 0.1,
          lambda_step_down: float = 0.05,
          no_improve_limit: int = 400,
          max_iter: int = 5000,
          seed: int = 42) -> dict:
    """
    Tabu Search Avanzado para CVRP.

    Returns dict: value, solution, iterations, time_s, history
    """
    rng = random.Random(seed)

    capacity  = instance_data['capacity']
    n_cust    = instance_data['n_customers']
    customers = instance_data['customers']
    dist      = instance_data['dist_matrix']
    demands   = {i + 1: customers[i][2] for i in range(n_cust)}

    routes    = _clarke_wright_init(n_cust, capacity, demands, dist)

    def copy_routes(r):
        return [list(x) for x in r]

    cur_cost    = _total_cost(routes, dist)
    best_routes = copy_routes(routes)
    best_cost   = cur_cost

    tabu_size = rng.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    freq       = {}   # freq[customer] = times relocated
    lam        = lambda_init
    no_improve = 0
    history    = [(0, best_cost)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = rng.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        best_pen   = float('inf')
        best_delta = float('inf')
        best_move  = None

        # Evaluate all neighborhoods with penalized objective
        for pen_d, actual_d, move_key, move_data in _relocate_moves(
                routes, demands, capacity, dist, freq, lam):
            is_tabu  = move_key in tabu_list
            new_cost = cur_cost + actual_d
            if is_tabu and new_cost >= best_cost:
                continue
            if pen_d < best_pen:
                best_pen   = pen_d
                best_delta = actual_d
                best_move  = (move_key, move_data)

        for pen_d, actual_d, move_key, move_data in _intra_two_opt(routes, dist):
            is_tabu  = move_key in tabu_list
            new_cost = cur_cost + actual_d
            if is_tabu and new_cost >= best_cost:
                continue
            if pen_d < best_pen:
                best_pen   = pen_d
                best_delta = actual_d
                best_move  = (move_key, move_data)

        for pen_d, actual_d, move_key, move_data in _inter_swap_moves(
                routes, demands, capacity, dist):
            is_tabu  = move_key in tabu_list
            new_cost = cur_cost + actual_d
            if is_tabu and new_cost >= best_cost:
                continue
            if pen_d < best_pen:
                best_pen   = pen_d
                best_delta = actual_d
                best_move  = (move_key, move_data)

        if best_move is None:
            history.append((it, best_cost))
            no_improve += 1
            if no_improve % 50 == 0:
                lam = min(lambda_max, lam + lambda_step_up)
            continue

        move_key, move_data = best_move
        mtype = move_data[0]

        if mtype == 'relocate':
            _, customer, ri, pos_rem, rj, ins_pos = move_data
            routes[ri].pop(pos_rem)
            routes[rj].insert(ins_pos, customer)
            routes = [r for r in routes if r]
            freq[customer] = freq.get(customer, 0) + 1

        elif mtype == '2opt_intra':
            _, ri, i, j = move_data
            routes[ri][i + 1:j + 1] = routes[ri][i + 1:j + 1][::-1]

        elif mtype == 'swap_inter':
            _, ri, pi, ci, rj, pj, cj = move_data
            routes[ri][pi] = cj
            routes[rj][pj] = ci
            freq[ci] = freq.get(ci, 0) + 1
            freq[cj] = freq.get(cj, 0) + 1

        cur_cost += best_delta
        tabu_list.append(move_key)

        if cur_cost < best_cost:
            best_routes = copy_routes(routes)
            best_cost   = cur_cost
            no_improve  = 0
            lam         = max(lambda_init, lam - lambda_step_down)
        else:
            no_improve += 1
            if no_improve % 50 == 0:
                lam = min(lambda_max, lam + lambda_step_up)

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
    print(f"{'Instance':<12} {'BKS':>8} {'TS-Avanz':>10} {'GAP%':>8} {'Routes':>7} {'Time(s)':>8}")
    print('-' * 60)
    for fp in vrp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data, max_iter=500)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10.1f} {gap:>7.2f}% "
              f"{len(res['solution']):>7} {res['time_s']:>8.4f}")
