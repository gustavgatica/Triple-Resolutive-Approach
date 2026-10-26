# ============================================================
# Modelo AMPL — Problema de Enrutamiento de Vehículos (CVRP)
# ============================================================
# Referencia: Laporte, G. (1992).
#   The vehicle routing problem: An overview of exact and
#   approximate algorithms.
#   European Journal of Operational Research, 59(3), 345–358.
#   https://doi.org/10.1016/0377-2217(92)90192-C
#
# Uso:
#   ampl: model cvrp.mod; data cvrp.dat; solve; display x;
# ============================================================

# --- Parámetros ---
param n;                        # Número de clientes
param K;                        # Número de vehículos disponibles
param Q;                        # Capacidad de cada vehículo
param d {1..n};                 # Demanda del cliente i
param c {0..n, 0..n};          # Costo de viajar de i a j (0 = depósito)

# --- Variables de decisión ---
var x {0..n, 0..n, 1..K} binary;
# x[i,j,k] = 1 si el vehículo k viaja directamente de i a j

# --- Función objetivo ---
minimize Costo_Rutas:
    sum {k in 1..K, i in 0..n, j in 0..n: i != j} c[i,j] * x[i,j,k];

# --- Restricciones ---
subject to Visita_Unica {i in 1..n}:
    sum {k in 1..K, j in 0..n: j != i} x[i,j,k] = 1;
# Cada cliente i es visitado exactamente una vez por algún vehículo.

subject to Flujo {p in 1..n, k in 1..K}:
    sum {i in 0..n} x[i,p,k] - sum {j in 0..n} x[p,j,k] = 0;
# Conservación de flujo: cada vehículo que entra a un nodo también debe salir.

subject to Salida_Deposito {k in 1..K}:
    sum {j in 1..n} x[0,j,k] <= 1;
# Cada vehículo parte del depósito como máximo una vez.

subject to Capacidad {k in 1..K}:
    sum {i in 1..n} d[i] * sum {j in 0..n} x[i,j,k] <= Q;
# La demanda total servida por cada vehículo no excede su capacidad Q.
