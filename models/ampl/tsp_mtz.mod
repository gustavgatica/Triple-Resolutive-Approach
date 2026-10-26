# ============================================================
# Modelo AMPL — Problema del Vendedor Viajero (TSP)
# Formulación de Miller-Tucker-Zemlin (MTZ)
# ============================================================
# Referencia: Miller, C. E., Tucker, A. W. & Zemlin, R. A. (1960).
#   Integer programming formulation of traveling salesman problems.
#   Journal of the ACM, 7(4), 326–329.
#   https://doi.org/10.1145/321043.321046
#
# Uso:
#   ampl: model tsp_mtz.mod; data tsp.dat; solve; display x;
# ============================================================

# --- Parámetros ---
param n;                            # Número de ciudades
param c {1..n, 1..n};              # Costo (distancia) de viajar de i a j

# --- Variables de decisión ---
var x {1..n, 1..n} binary;         # x[i,j] = 1 si el recorrido incluye el arco i→j
var u {2..n} >= 0, <= n - 1;       # Variables auxiliares MTZ para eliminar subtours

# --- Función objetivo ---
minimize Costo_Total:
    sum {i in 1..n, j in 1..n: i != j} c[i,j] * x[i,j];

# --- Restricciones ---
subject to Llegada {j in 1..n}:
    sum {i in 1..n: i != j} x[i,j] = 1;
# Cada ciudad j tiene exactamente un arco de entrada.

subject to Salida {i in 1..n}:
    sum {j in 1..n: j != i} x[i,j] = 1;
# Cada ciudad i tiene exactamente un arco de salida.

subject to Subtour {i in 2..n, j in 2..n: i != j}:
    u[i] - u[j] + n * x[i,j] <= n - 1;
# Restricción MTZ: elimina subtours imponiendo un orden de visita.
# u[i] representa el orden ordinal en que se visita la ciudad i.
# Si x[i,j]=1, entonces u[j] >= u[i]+1, garantizando un único tour hamiltoniano.
