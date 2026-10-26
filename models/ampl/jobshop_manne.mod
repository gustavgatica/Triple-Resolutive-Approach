# ============================================================
# Modelo AMPL — Job Shop Scheduling (JSSP)
# Formulación Disyuntiva de Manne
# ============================================================
# Referencia: Manne, A. S. (1960).
#   On the job-shop scheduling problem.
#   Operations Research, 8(2), 219–223.
#   https://doi.org/10.1287/opre.8.2.219
#
# Uso:
#   ampl: model jobshop_manne.mod; data jobshop.dat; solve; display Cmax;
# ============================================================

# --- Parámetros ---
param n;                                # Número de trabajos
param m;                                # Número de máquinas
param p {1..n, 1..m};                  # Tiempo de procesamiento: operación (i,j)
param route {1..n, 1..m};              # route[i,k] = máquina usada en la k-ésima
                                        # operación del trabajo i
param M := 1e6;                         # Constante Big-M (suficientemente grande)

# --- Variables de decisión ---
var S {1..n, 1..m} >= 0;               # S[i,j] = tiempo de inicio de la operación
                                        # del trabajo i en la máquina j
var y {i in 1..n, k in 1..m,
       j in 1..n, l in 1..m:
       i < j and route[i,k] = route[j,l]} binary;
# y[i,k,j,l] = 1 si la operación (i,k) precede a (j,l) en la misma máquina
var Cmax >= 0;                          # Makespan

# --- Función objetivo ---
minimize Makespan: Cmax;

# --- Restricciones ---
subject to Def_Makespan {i in 1..n, k in 1..m}:
    S[i, route[i,k]] + p[i, route[i,k]] <= Cmax;
# El makespan es mayor o igual al tiempo de finalización de toda operación.

subject to Precedencia {i in 1..n, k in 1..m-1}:
    S[i, route[i,k+1]] >= S[i, route[i,k]] + p[i, route[i,k]];
# Cada trabajo respeta la ruta tecnológica: la operación k+1 comienza
# solo cuando finaliza la operación k.

subject to Disyuncion1 {i in 1..n, k in 1..m,
                         j in 1..n, l in 1..m:
                         i < j and route[i,k] = route[j,l]}:
    S[j, route[j,l]] >= S[i, route[i,k]] + p[i, route[i,k]] - M * (1 - y[i,k,j,l]);
# Si y=1: operación (i,k) precede a (j,l) → (j,l) no puede iniciar antes de que
# (i,k) finalice. Si y=0: esta restricción se desactiva (Big-M).

subject to Disyuncion2 {i in 1..n, k in 1..m,
                         j in 1..n, l in 1..m:
                         i < j and route[i,k] = route[j,l]}:
    S[i, route[i,k]] >= S[j, route[j,l]] + p[j, route[j,l]] - M * y[i,k,j,l];
# Si y=0: operación (j,l) precede a (i,k). Si y=1: esta restricción se desactiva.
# Juntas, las dos restricciones disyuntivas garantizan que en cada máquina
# no haya solapamiento entre operaciones.
