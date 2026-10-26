# Nivel 3 - TS-Avanzado (TSP): los tres mecanismos de memoria de largo
# plazo que diferencian este nivel del anterior.
# Fuente: tabu_search/tsp/ts_avanzado.py

# (a) MEMORIA DE FRECUENCIA: freq[a][b] cuenta cuantas veces la arista
#     (a,b) ha sido eliminada por un movimiento 2-opt.
freq = [[0] * n for _ in range(n)]

for it in range(1, max_iter + 1):

    # (b) LISTA TABU DINAMICA: el tamano se re-sortea cada 150 iteraciones
    #     dentro del rango [7, 25].
    if it % change_every == 0:
        new_size  = rng.randint(tabu_min, tabu_max)
        tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

    # (c) REINICIO INFORMADO: perturbacion double-bridge (4-opt) sobre la
    #     mejor solucion cuando el estancamiento supera el limite.
    if no_improve >= no_improve_limit:
        current    = _perturb_double_bridge(best[:], rng)
        cur_cost   = _tour_cost(current, dist)
        tabu_list.clear()
        no_improve = 0

    for i in range(n - 1):
        for j in range(i + 2, n):
            delta = _two_opt_delta(current, i, j, dist)
            move  = (min(current[i], current[j]), max(current[i], current[j]))

            if move in tabu_list and cur_cost + delta >= best_cost:
                continue

            # PENALIZACION ADAPTATIVA: encarece los movimientos que
            # eliminan aristas ya eliminadas muchas veces, empujando la
            # busqueda hacia regiones poco exploradas.
            a, b = current[i], current[(i + 1) % n]
            c, d = current[j], current[(j + 1) % n]
            pen_delta = delta + lam * (freq[a][b] + freq[c][d])

            if pen_delta < best_penalized:
                best_penalized = pen_delta
                best_move      = (i, j, move, a, b, c, d)

    # Actualizar la frecuencia de las aristas efectivamente eliminadas
    freq[a][b] += 1; freq[b][a] += 1
    freq[c][d] += 1; freq[d][c] += 1

    # lambda ADAPTATIVO: sube al estancarse (diversifica), baja al mejorar
    # (intensifica).
    if cur_cost < best_cost:
        best, best_cost = current[:], cur_cost
        no_improve = 0
        lam = max(lambda_init, lam - lambda_step_down)
    else:
        no_improve += 1
        if no_improve % 50 == 0:
            lam = min(lambda_max, lam + lambda_step_up)
