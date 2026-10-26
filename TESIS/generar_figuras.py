"""
Genera las figuras propias del documento de tesis (carpeta TESIS/figuras/).

Fuente de datos: results/tabla_consolidada.csv del repositorio.
Los valores agregados coinciden con la Tabla "Análisis global" del paper.

Uso:
    python TESIS/generar_figuras.py
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "results", "tabla_consolidada.csv")
SALIDA = os.path.join(RAIZ, "TESIS", "figuras")
os.makedirs(SALIDA, exist_ok=True)

COLORES = ["#B0BEC5", "#64B5F6", "#1A5490"]
NIVELES = ["TS-Básico", "TS-Intermedio", "TS-Avanzado"]

# GAP promedio por problema (Tabla de análisis global del paper)
GAP = {
    "Knapsack": [0.22, 0.13, 0.10],
    "TSP":      [2.42, 2.15, 1.22],
    "CVRP":     [19.22, 7.72, 6.38],
    "Flowshop": [1.74, 1.74, 1.75],
    "Job Shop": [8.89, 8.24, 7.52],
}
GAP_GLOBAL = [6.50, 4.00, 3.40]

# Tiempo promedio (s) por problema
TIEMPO = {
    "Knapsack": [0.01, 0.02, 0.07],
    "TSP":      [1.91, 4.09, 8.39],
    "CVRP":     [2.93, 9.21, 69.25],
    "Flowshop": [3.73, 7.50, 9.13],
    "Job Shop": [16.05, 5.91, 8.68],
}


def fig_gap_por_problema():
    """Barras agrupadas: GAP por problema y nivel de TS (escala log)."""
    problemas = list(GAP.keys())
    x = range(len(problemas))
    ancho = 0.26

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for k, nivel in enumerate(NIVELES):
        valores = [GAP[p][k] for p in problemas]
        pos = [i + (k - 1) * ancho for i in x]
        barras = ax.bar(pos, valores, ancho, label=nivel,
                        color=COLORES[k], edgecolor="black", linewidth=0.4)
        ax.bar_label(barras, fmt="%.2f", fontsize=6.5, padding=1.5)

    ax.set_yscale("log")
    ax.set_ylabel("GAP promedio respecto al BKS (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(problemas)
    ax.legend(frameon=False, ncol=3, fontsize=8, loc="upper center",
              bbox_to_anchor=(0.5, 1.16))
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "gap_por_problema.pdf"),
                bbox_inches="tight")
    plt.close(fig)


def fig_gap_global():
    """Progresión del GAP global entre los tres niveles de TS."""
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    barras = ax.bar(NIVELES, GAP_GLOBAL, 0.5,
                    color=COLORES, edgecolor="black", linewidth=0.4)
    ax.bar_label(barras, fmt="%.2f %%", fontsize=9, padding=3)

    # Anotación de la reducción relativa acumulada
    ax.annotate("", xy=(2, GAP_GLOBAL[2] + 0.9), xytext=(0, GAP_GLOBAL[0] + 0.9),
                arrowprops=dict(arrowstyle="->", color="#B00020", lw=1.1))
    ax.text(1, GAP_GLOBAL[0] + 1.25, "-48 % relativo", ha="center",
            fontsize=8.5, color="#B00020")

    ax.set_ylabel("GAP global promedio (%)")
    ax.set_ylim(0, 8.2)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "gap_global.pdf"), bbox_inches="tight")
    plt.close(fig)


def fig_calidad_vs_tiempo():
    """Compromiso calidad/costo: GAP global frente a tiempo total."""
    tiempo_total = [sum(TIEMPO[p][k] for p in TIEMPO) for k in range(3)]

    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for k, nivel in enumerate(NIVELES):
        ax.scatter(tiempo_total[k], GAP_GLOBAL[k], s=130, color=COLORES[k],
                   edgecolor="black", linewidth=0.6, zorder=3, label=nivel)
    ax.plot(tiempo_total, GAP_GLOBAL, color="#90A4AE", linestyle="--",
            linewidth=1, zorder=2)

    for k, nivel in enumerate(NIVELES):
        ax.annotate(nivel, (tiempo_total[k], GAP_GLOBAL[k]),
                    textcoords="offset points", xytext=(8, 8), fontsize=8)

    ax.set_xlabel("Tiempo acumulado sobre los cinco problemas (s)")
    ax.set_ylabel("GAP global promedio (%)")
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "calidad_vs_tiempo.pdf"),
                bbox_inches="tight")
    plt.close(fig)


def fig_dispersion_semillas():
    """Desviación estándar del GAP por instancia y nivel (estabilidad)."""
    df = pd.read_csv(CSV)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))

    etiquetas = df["Instancia"].tolist()
    x = range(len(etiquetas))
    for k, (col, nivel) in enumerate(
            zip(["GAP_B_std", "GAP_I_std", "GAP_A_std"], NIVELES)):
        ax.plot(list(x), df[col], marker="o", markersize=3.5, linewidth=1,
                color=COLORES[k], label=nivel)

    ax.set_ylabel("Desviación estándar del GAP (pp)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(etiquetas, rotation=60, ha="right", fontsize=6.5)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "dispersion_semillas.pdf"),
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_gap_por_problema()
    fig_gap_global()
    fig_calidad_vs_tiempo()
    fig_dispersion_semillas()
    print(f"Figuras generadas en {SALIDA}")
