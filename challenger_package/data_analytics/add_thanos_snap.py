import numpy as np
import csv
import statsmodels.api as sm
import datetime
import sys

def get_resource_data():
    with open("../cleaned_avengers_data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

# def simulate_paths(N, T, start_levels, beta1, sigma, alpha, z_empirical):
#     t = np.arange(1, T + 1)
#     paths = np.zeros((N, T))
#     for i in range(N):
#         z = np.random.choice(z_empirical, size=T, replace=True)
#         noise = sigma * (t ** (alpha / 2)) * z
#         paths[i] = start_levels[i] + beta1 * t + noise
#     return paths

def simulate_paths(N, T, start_levels, beta1, sigma, alpha, z_empirical):
    t = np.arange(1, T + 1)
    paths = np.zeros((N, T))
    for i in range(N):
        z = np.random.randn(T)  # fresh standard normal, not recycled empirical
        noise = sigma * (t ** (alpha / 2)) * z
        paths[i] = start_levels[i] + beta1 * t + noise
    return paths

# =====================================================
# PARSE ARGS
# =====================================================

params = sys.argv[1:]
M = int(params[0])
snapped = params[1].lower() == "true"

# =====================================================
# LOAD AND STRUCTURE DATA
# =====================================================

data_dict = get_resource_data()
print("Keys:", data_dict[0].keys())
data_dict = data_dict[:500*5]

# Each row is one resource at one timestep.
# Figure out how many unique resources there are (group_size).
sectors = list(dict.fromkeys(row["sector_id"] for row in data_dict))
resources = list(dict.fromkeys(row["resource_type"] for row in data_dict))
group_size = len(resources)
print(f"group_size={group_size}, total rows={len(data_dict)}")

T_total = len(data_dict) // group_size

# Build data matrix: shape (group_size, T_total)
# Row i = time series for resource i
data_matrix = np.zeros((group_size, T_total))
for t_idx in range(T_total):
    for r_idx in range(group_size):
        row = data_dict[t_idx * group_size + r_idx]
        data_matrix[r_idx, t_idx] = float(row["stock_level"])

# =====================================================
# APPLY SNAP TO LAST TIMESTEP IF REQUESTED
# =====================================================

# snapped_point: the starting beta0s for simulation
# = stock levels at the last observed timestep, halved if snapped
snapped_point = data_matrix[:, -1].copy()
if snapped:
    snapped_point *= 0.5

# Use all data for fitting
data = data_matrix  # shape (group_size, T_total)
N_fit = group_size
t = np.arange(1, T_total + 1)


# =====================================================
# 1. ESTIMATE COMMON LINEAR TREND
# =====================================================

# Stack all datasets
y_stack = data.flatten()
t_stack = np.tile(t, N_fit)

X = sm.add_constant(t_stack)
trend_model = sm.OLS(y_stack, X).fit()

beta0, beta1 = trend_model.params

print("=== Trend Estimates ===")
print("beta0 =", beta0)
print("beta1 =", beta1)

# =====================================================
# 2. REMOVE TREND
# =====================================================

trend = beta0 + beta1 * t
residuals = data - trend   # broadcasting over rows

# =====================================================
# 3. ESTIMATE TIME-VARYING VARIANCE
# =====================================================

# Cross-sectional variance at each time t
var_t = np.var(residuals, axis=0, ddof=1)

# =====================================================
# 4. FIT POWER LAW: Var = sigma^2 * t^alpha
# =====================================================

eps = 1e-8  # avoid log(0)

# Replace the alpha estimation block with this
diffs = np.diff(data, axis=1)           # shape (group_size, T_total-1)
t_mid = (t[:-1] + t[1:]) / 2.0

# Var(diff at t) ~ 2 * sigma^2 * t^alpha
# Take log: log(diff^2) ~ log(2*sigma^2) + alpha*log(t)
diff_sq = diffs ** 2
log_diff_sq = np.log(diff_sq.flatten() + eps)
log_t_mid = np.log(np.tile(t_mid, group_size))

X_var = sm.add_constant(log_t_mid)
var_model = sm.OLS(log_diff_sq, X_var).fit()
log_sigma2_hat, alpha_hat = var_model.params

# Correct for the factor of 2: Var(diff) = 2*sigma^2*t^alpha
sigma2_hat = np.mean(diff_sq / (2.0 * np.tile(t_mid, (group_size, 1)) ** alpha_hat))
sigma_hat = np.sqrt(sigma2_hat)

print("\n=== Variance Estimates ===")
print("alpha =", alpha_hat)
print("sigma =", sigma_hat)

# =====================================================
# 4.5. BUILD EMPIRICAL SHOCK DISTRIBUTION
# =====================================================

t_matrix = np.tile(t, (N_fit, 1))  # shape (N, T)

# Recompute scaled residuals using the corrected sigma_hat
scaled_residuals = residuals / (sigma_hat * (t_matrix ** (alpha_hat/2)))
z_empirical = scaled_residuals.flatten()
z_empirical = z_empirical - np.mean(z_empirical)
z_empirical = z_empirical / np.std(z_empirical)

lower = np.percentile(z_empirical, 0.25)
upper = np.percentile(z_empirical, 99.75)
z_empirical_trimmed = z_empirical[
    (z_empirical >= lower) & (z_empirical <= upper)
]

# =====================================================
# 5. SIMULATE FUTURE PATHS
# =====================================================

# Generate simulated datasets
simulated_data = simulate_paths(
    N_fit, M, snapped_point, beta1, sigma_hat, alpha_hat, z_empirical_trimmed
)

# =====================================================
# 6. WRITE OUTPUT
# =====================================================

start_dt = datetime.datetime.fromisoformat(data_dict[-1]["timestamp"])

with open("../avengers_data_with_snap.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=data_dict[0].keys())
    writer.writeheader()

    # Write original data
    for row in data_dict:
        writer.writerow(row)

    # Write simulated future data
    for step in range(M):
        new_dt = start_dt + datetime.timedelta(minutes=12 * (step + 1))
        for r_idx in range(group_size):
            new_row = data_dict[-group_size + r_idx].copy()
            new_row["timestamp"] = new_dt.strftime("%Y-%m-%dT%H:%M:%S")
            new_row["stock_level"] = str(max(0.0, simulated_data[r_idx, step]))
            new_row["snap_event_detected"] = "False"
            writer.writerow(new_row)

print(f"\nWrote {len(data_dict) + M * group_size} rows to avengers_data_with_snap.csv")

print("sigma_hat =", sigma_hat)
print("z std before norm =", np.std(scaled_residuals))
print("z std after norm =", np.std(z_empirical_trimmed))
print("noise at t=1 magnitude =", sigma_hat * (1 ** (alpha_hat/2)))
print(f'snapped_point[0] = {snapped_point[0]}')
print(f'simulated_data[0, :5] = {simulated_data[0, :5]}')
print("simulated_data[0, :10] std rolling:", 
      [np.std(simulated_data[0, max(0,i-20):i+1]) for i in range(20, 500, 50)])
print("alpha_hat =", alpha_hat)