"""
main.py — CLI principal del repositorio Triple Enfoque Resolutivo.

Uso:
  # Un experimento específico
  python src/main.py --problema tsp --instancia berlin52 --algoritmo ts_basico

  # Todos los experimentos de un problema
  python src/main.py --problema tsp --all-instances --all-algoritmos

  # Los 72 experimentos completos con una semilla
  python src/main.py --all

  # Los 360 experimentos completos con 5 semillas (recomendado para el paper)
  python src/main.py --all --multi-seed

  # Solo generar reporte (sin ejecutar experimentos)
  python src/main.py --report
"""

from __future__ import annotations

import sys
import os
import argparse
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.runner   import run_experiment, PROBLEMS, ALGORITHMS, INSTANCES_DIR, EXTENSIONS
from src.reporter import generate_report

# ---------------------------------------------------------------------------
# Semillas para validación estadística
# ---------------------------------------------------------------------------

DEFAULT_SEEDS = [42, 123, 456, 789, 1337]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_instances(problema: str) -> list[str]:
    """Devuelve los nombres de instancias disponibles para un problema."""
    ext     = EXTENSIONS[problema]
    folder  = os.path.join(INSTANCES_DIR, problema)
    if not os.path.isdir(folder):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(folder)
        if f.endswith(ext)
    )


def run_all(seeds: list[int] | None = None, verbose: bool = True) -> None:
    """
    Ejecuta todos los experimentos (5 prob × instancias × 3 alg × semillas).

    Con seeds=[42]          → 72 experimentos (comportamiento original).
    Con seeds=DEFAULT_SEEDS → 360 experimentos, permite calcular media ± std.
    """
    if seeds is None:
        seeds = [42]

    n_seeds  = len(seeds)
    t0       = time.perf_counter()
    total    = 0
    failed   = []
    expected = len(PROBLEMS) * 5 * len(ALGORITHMS) * n_seeds

    print("\n" + "=" * 60)
    print(f"  TRIPLE ENFOQUE RESOLUTIVO — {expected} Experimentos")
    print(f"  Semillas: {seeds}")
    print("=" * 60)

    for seed in seeds:
        print(f"\n{'-'*60}")
        print(f"  SEMILLA {seed}  ({seeds.index(seed)+1}/{n_seeds})")
        print(f"{'-'*60}")

        for prob in PROBLEMS:
            instances = _list_instances(prob)
            print(f"\n  [{prob.upper()}] — {len(instances)} inst × {len(ALGORITHMS)} alg")

            for inst in instances:
                for alg in ALGORITHMS:
                    try:
                        run_experiment(prob, inst, alg, seed=seed, verbose=verbose)
                        total += 1
                    except Exception as e:
                        print(f"  ERROR: {prob}/{inst}/{alg} (seed={seed}) → {e}")
                        failed.append((prob, inst, alg, seed, str(e)))

    elapsed = time.perf_counter() - t0
    print("\n" + "=" * 60)
    print(f"  Completados: {total} / {expected} experimentos")
    print(f"  Tiempo total: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    if failed:
        print(f"  Fallidos ({len(failed)}):")
        for item in failed:
            print(f"    {item[0]}/{item[1]}/{item[2]} seed={item[3]}: {item[4]}")
    print("=" * 60)

    print("\nGenerando reportes...")
    generate_report(verbose=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Triple Enfoque Resolutivo — CLI de experimentos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--problema',       choices=PROBLEMS,   help='Problema a resolver')
    parser.add_argument('--instancia',      help='Nombre de la instancia (sin extensión)')
    parser.add_argument('--algoritmo',      choices=ALGORITHMS, help='Algoritmo Tabu Search')
    parser.add_argument('--all',            action='store_true', help='Ejecutar todos los experimentos')
    parser.add_argument('--multi-seed',     action='store_true',
                        help=f'Usar {len(DEFAULT_SEEDS)} semillas: {DEFAULT_SEEDS} (para media±std)')
    parser.add_argument('--all-instances',  action='store_true', help='Todas las instancias del problema')
    parser.add_argument('--all-algoritmos', action='store_true', help='Todos los algoritmos')
    parser.add_argument('--report',         action='store_true', help='Solo generar reporte')
    parser.add_argument('--seed',           type=int, default=42,
                        help='Semilla única (se ignora si se usa --multi-seed)')
    parser.add_argument('--list',           action='store_true', help='Listar instancias disponibles')

    args = parser.parse_args()

    # Listar instancias
    if args.list:
        prob = args.problema or 'tsp'
        insts = _list_instances(prob)
        print(f"\nInstancias disponibles para [{prob}]:")
        for i in insts:
            print(f"  {i}")
        return

    # Solo reporte
    if args.report:
        generate_report()
        return

    # Todos los experimentos
    if args.all:
        seeds = DEFAULT_SEEDS if args.multi_seed else [args.seed]
        run_all(seeds=seeds)
        return

    # Validación para experimento individual o parcial
    if not args.problema:
        parser.error("Especifica --problema o usa --all")

    # Determinar instancias
    if args.all_instances:
        instances = _list_instances(args.problema)
    elif args.instancia:
        instances = [args.instancia]
    else:
        parser.error("Especifica --instancia o --all-instances")

    # Determinar algoritmos
    if args.all_algoritmos:
        algoritmos = ALGORITHMS
    elif args.algoritmo:
        algoritmos = [args.algoritmo]
    else:
        parser.error("Especifica --algoritmo o --all-algoritmos")

    # Ejecutar
    print(f"\nEjecutando {len(instances) * len(algoritmos)} experimento(s)...")
    for inst in instances:
        for alg in algoritmos:
            try:
                res = run_experiment(args.problema, inst, alg,
                                     seed=args.seed, verbose=True)
            except Exception as e:
                print(f"  ERROR: {e}")

    # Generar reporte si se corrieron varios
    if len(instances) * len(algoritmos) > 1:
        print("\nActualizando reportes...")
        generate_report(verbose=False)
        print("✓ Reportes actualizados en results/")


if __name__ == '__main__':
    main()
