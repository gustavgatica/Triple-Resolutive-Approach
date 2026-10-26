"""
generar_taillard.py — Regenera las instancias de Flowshop de Taillard (1993).

Uso:
  python instances/flowshop/generar_taillard.py

Las instancias de Taillard se definen por su semilla: los tiempos de proceso
se obtienen con el generador congruencial lineal publicado en
  E. Taillard, "Benchmarks for basic scheduling problems",
  European Journal of Operational Research 64 (1993) 278-285.
Las semillas son las de la primera instancia de cada clase (tai20_5,
tai20_10, tai20_20, tai50_5 y tai50_10). Los BKS son los makespan óptimos
conocidos de esas instancias.
"""

from __future__ import annotations

import os

_HERE = os.path.dirname(os.path.abspath(__file__))

# nombre: (trabajos, máquinas, semilla de tiempos, BKS)
INSTANCIAS = {
    'ta001': (20, 5, 873654221, 1278),
    'ta011': (20, 10, 587595453, 1582),
    'ta021': (20, 20, 479340445, 2297),
    'ta031': (50, 5, 1328042058, 2724),
    'ta041': (50, 10, 1958948863, 2991),
}


def generar(n_jobs: int, n_machines: int, seed: int) -> list[list[int]]:
    """Devuelve p[trabajo][máquina] con el generador de Taillard."""
    def unif(low: int, high: int) -> int:
        nonlocal seed
        k = seed // 127773
        seed = 16807 * (seed % 127773) - k * 2836
        if seed < 0:
            seed += 2147483647
        return low + int(seed / 2147483647 * (high - low + 1))

    # Taillard genera por máquina y, dentro de cada máquina, por trabajo.
    por_maquina = [[unif(1, 99) for _ in range(n_jobs)] for _ in range(n_machines)]
    return [[por_maquina[i][j] for i in range(n_machines)] for j in range(n_jobs)]


def main() -> None:
    for name, (n_jobs, n_machines, seed, bks) in INSTANCIAS.items():
        p = generar(n_jobs, n_machines, seed)
        path = os.path.join(_HERE, f'{name}.fsp')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# Taillard Flowshop {name}: n={n_jobs} jobs, '
                    f'm={n_machines} machines  BKS={bks}\n')
            f.write(f'# Semilla de Taillard: {seed}\n')
            f.write(f'{n_jobs} {n_machines}\n')
            for fila in p:
                f.write('  '.join(str(v) for v in fila) + '\n')
        print(f'  OK {path}')


if __name__ == '__main__':
    main()
