# El orquestador recorre el producto cartesiano
# (problema x instancia x algoritmo x semilla) y persiste cada corrida.
# Con una semilla son 72 experimentos; con las cinco, 360.
# Fuente: src/main.py

DEFAULT_SEEDS = [42, 123, 456, 789, 1337]


def run_all(seeds: list[int] | None = None, verbose: bool = True) -> None:
    """
    Con seeds=[42]          -> 72 experimentos (una corrida por combinacion).
    Con seeds=DEFAULT_SEEDS -> 360 experimentos, permite media +/- desv. est.
    """
    if seeds is None:
        seeds = [42]

    for seed in seeds:
        for problema in PROBLEMS:
            for instancia in _list_instances(problema):
                for algoritmo in ALGORITHMS:
                    run_experiment(problema, instancia, algoritmo, seed=seed)


# Interfaz de linea de comandos
parser.add_argument('--problema',   choices=PROBLEMS)
parser.add_argument('--instancia')
parser.add_argument('--algoritmo',  choices=ALGORITHMS)
parser.add_argument('--all',        action='store_true')
parser.add_argument('--multi-seed', action='store_true')
parser.add_argument('--report',     action='store_true')
parser.add_argument('--seed',       type=int, default=42)
