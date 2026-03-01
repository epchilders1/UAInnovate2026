import numpy as np
from collect_data import get_resource_data
import statsmodels.api as sm
import matplotlib.pyplot as plt

def get_stock_data():
    stock_data = get_resource_data()
    sectors = ["New Asgard", "Sanctum Sanctorum"]
    data = []

    for sector in sectors:
        for resource in stock_data[sector].keys():
            r_stock_data = stock_data[sector][resource]
            r_stock_level = [r_stock_data["stock_level"][i] if not r_stock_data["snap_event_detected"][i] else 2 * r_stock_data["stock_level"][i] for i in range(1500)]
            data.append(r_stock_level)
    return data

data = np.array(get_stock_data())

N, T = data.shape
t = np.arange(1, T + 1)

# =====================================================
# 1. ESTIMATE COMMON LINEAR TREND
# =====================================================

# Stack all datasets
y_stack = data.flatten()
t_stack = np.tile(t, N)

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

log_var = np.log(var_t + eps)
log_t = np.log(t)

X_var = sm.add_constant(log_t)
var_model = sm.OLS(log_var, X_var).fit()

log_sigma2_hat, alpha_hat = var_model.params
sigma2_hat = np.mean(var_t / (t ** alpha_hat))
sigma_hat = np.sqrt(sigma2_hat)

print("\n=== Variance Estimates ===")
print("alpha =", alpha_hat)
print("sigma =", sigma_hat)

# =====================================================
# 4.5. BUILD EMPIRICAL SHOCK DISTRIBUTION
# =====================================================

t_matrix = np.tile(t, (N, 1))  # shape (N, T)

scaled_residuals = residuals / (sigma_hat * (t_matrix ** (alpha_hat/2)))

# Flatten to 1D empirical distribution
z_empirical = scaled_residuals.flatten()

# Optional but recommended: center and normalize to unit variance
z_empirical = z_empirical - np.mean(z_empirical)
z_empirical = z_empirical / np.std(z_empirical)

lower = np.percentile(z_empirical, 0.25)
upper = np.percentile(z_empirical, 99.75)

z_empirical_trimmed = z_empirical[
    (z_empirical >= lower) & (z_empirical <= upper)
]

# =====================================================
# 5. SIMULATION FUNCTION
# =====================================================

def simulate_paths(N, T, beta0, beta1, sigma, alpha, z_empirical):
    t = np.arange(1, T + 1)
    paths = np.zeros((N, T))

    for i in range(N):
        z = np.random.choice(z_empirical, size=T, replace=True)

        noise = sigma * (t ** (alpha / 2)) * z
        paths[i] = beta0 + beta1 * t + noise

    return paths

# Generate simulated datasets
simulated_data = simulate_paths(
    N, T, beta0, beta1, sigma_hat, alpha_hat, z_empirical_trimmed
)

# =====================================================
# 6. DIAGNOSTIC PLOTS
# =====================================================

plt.figure()
plt.plot(t, var_t)
plt.title("Cross-Sectional Variance vs Time")
plt.xlabel("Time")
plt.ylabel("Variance")
plt.show()

plt.figure()
plt.plot(log_t, log_var)
plt.title("Log-Log Variance Fit")
plt.xlabel("log(Time)")
plt.ylabel("log(Variance)")
plt.show()

plt.figure()
plt.plot(t, data[0], label="New Asgard example")
plt.plot(t, data[1], label="Sanctum Sanctorum example")
plt.plot(t, simulated_data[0], label="Simulated example")
plt.legend()
plt.title("Original vs Simulated Path")
plt.show()