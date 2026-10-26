# ============================================================
# Modelo AMPL — Problema de la Mochila (0-1 Knapsack)
# ============================================================
# Referencia: Martello, S. & Toth, P. (1990).
#   Knapsack Problems: Algorithms and Computer Implementations.
#   John Wiley & Sons.
#
# Uso:
#   ampl: model knapsack.mod; data knapsack.dat; solve; display x;
# ============================================================

# --- Parámetros ---
param n;                    # Número de artículos disponibles
param W;                    # Capacidad máxima de la mochila
param p {1..n};             # Beneficio (profit) de cada artículo i
param w {1..n};             # Peso de cada artículo i

# --- Variables de decisión ---
var x {1..n} binary;        # x[i] = 1 si el artículo i es incluido, 0 si no

# --- Función objetivo ---
maximize Beneficio_Total:
    sum {i in 1..n} p[i] * x[i];

# --- Restricciones ---
subject to Capacidad:
    sum {i in 1..n} w[i] * x[i] <= W;
# La suma de pesos de los artículos seleccionados no puede
# exceder la capacidad máxima W de la mochila.
