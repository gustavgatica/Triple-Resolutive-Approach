# Nivel 1 - TS-Basico (TSP): lista tabu de tamano FIJO sobre pares de
# aristas, vecindad 2-opt completa y criterio de aspiracion elemental.
# Fuente: tabu_search/tsp/ts_basico.py

tabu_list = deque(maxlen=tabu_size)          # tamano fijo: 10

for it in range(1, max_iter + 1):
    best_delta = float('inf')
    best_move  = None

    # --- Explorar la vecindad 2-opt completa ---
    for i in range(n - 1):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue                      # movimiento nulo en tour circular

            delta = _two_opt_delta(current, i, j, dist)
            move  = (min(current[i], current[j]),
                     max(current[i], current[j]))   # arista canonica

            is_tabu  = move in tabu_list
            new_cost = cur_cost + delta

            # Aspiracion: se admite un movimiento tabu solo si mejora
            # el mejor global conocido.
            if is_tabu and new_cost >= best_cost:
                continue

            if delta < best_delta:
                best_delta = delta
                best_move  = (i, j, move)

    i, j, move = best_move
    current[i + 1:j + 1] = current[i + 1:j + 1][::-1]   # aplicar 2-opt
    cur_cost += best_delta
    tabu_list.append(move)

    if cur_cost < best_cost:
        best      = current[:]
        best_cost = cur_cost

    history.append((it, best_cost))
