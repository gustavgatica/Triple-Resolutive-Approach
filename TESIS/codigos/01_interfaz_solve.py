# Interfaz uniforme: los quince modulos exponen la misma firma y devuelven
# el mismo diccionario, de modo que el orquestador puede tratar los cinco
# problemas de forma homogenea.
# Fuente: tabu_search/{problema}/ts_{nivel}.py

def solve(instance_data: dict,
          tabu_size: int = 10,
          max_iter: int = 1000,
          seed: int = 42) -> dict:
    """
    Returns
    -------
    dict with keys:
        value     : best value found
        solution  : best solution encoding
        iterations: number of iterations executed
        time_s    : elapsed time in seconds
        history   : list of (iteration, best_value) tuples
    """
    # ... construccion de la solucion inicial y bucle de busqueda tabu ...
    return {
        'value':      best_cost,
        'solution':   best,
        'iterations': it,
        'time_s':     elapsed,
        'history':    history,
    }
