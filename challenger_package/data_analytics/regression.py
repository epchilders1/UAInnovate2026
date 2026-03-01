import numpy as np
import matplotlib.pyplot as plt
from collect_data import get_resource_data


def compute_weights(T, t_snap=None):
    t = np.arange(T, dtype=float)
    if t_snap is None:
        w = 1.0 / (t + 1)
    else:
        n_post = T - t_snap
        safe_denom = np.where(t >= t_snap, t - t_snap + 1.0, 1.0)
        post_weight = np.where(t >= t_snap, 1.0 / safe_denom, 0.0)
        pre_weight  = np.where(t < t_snap, 1.0 / (t_snap * n_post), 0.0)
        w = pre_weight + post_weight
    return w / w.sum()


def fit_stockout_model(stock_levels, t_snap=None, lambda_ridge=1.0):
    T = len(stock_levels)
    t = np.arange(T, dtype=float)
    y = stock_levels.astype(float)
    w = compute_weights(T, t_snap)
    W = np.diag(w)

    if t_snap is not None:
        S = (t >= t_snap).astype(float)
        X = np.column_stack([np.ones(T), t, S])
        P = lambda_ridge * np.diag([0.0, 1.0, 0.0])  # only penalize beta
    else:
        X = np.column_stack([np.ones(T), t])
        P = lambda_ridge * np.diag([0.0, 1.0])  # only penalize beta

    A = X.T @ W @ X + P
    b = X.T @ W @ y
    theta = np.linalg.solve(A, b)

    n_params = len(theta)
    residuals = y - X @ theta
    sigma2 = np.sum(w * residuals**2) / (T - n_params)
    cov_theta = sigma2 * np.linalg.inv(A)

    if t_snap is not None:
        alpha, beta, gamma = theta
        t_star = -(alpha + gamma) / beta
        grad = np.array([-1.0/beta, (alpha+gamma)/beta**2, -1.0/beta])
    else:
        alpha, beta = theta
        gamma = 0.0
        t_star = -alpha / beta
        grad = np.array([-1.0/beta, alpha/beta**2])

    var_tstar = grad @ cov_theta @ grad
    std_tstar = np.sqrt(max(var_tstar, 0))

    return {
        "theta": theta,
        "t_star": t_star,
        "t_star_std": std_tstar,
        "ci_95": (t_star - 1.96*std_tstar, t_star + 1.96*std_tstar),
        "alpha": alpha, "beta": beta, "gamma": gamma,
        "sigma2": sigma2, "cov_theta": cov_theta, "weights": w,
    }

def fit_stockout_model_theil_sen(stock_levels, t_snap=None):
    T = len(stock_levels)
    t = np.arange(T, dtype=float)
    y = stock_levels.astype(float)

    if t_snap is not None:
        t_pre, y_pre = t[t < t_snap], y[t < t_snap]
        t_post, y_post = t[t >= t_snap], y[t >= t_snap]

        def theil_sen_slope(tx, yx):
            slopes = []
            n = len(tx)
            for i in range(n):
                for j in range(i+1, n):
                    slopes.append((yx[j] - yx[i]) / (tx[j] - tx[i]))
            return np.median(slopes)

        beta_pre  = theil_sen_slope(t_pre, y_pre)
        beta_post = theil_sen_slope(t_post, y_post)
        n_pre, n_post = len(t_pre), len(t_post)
        beta = (beta_pre * n_pre + beta_post * n_post) / (n_pre + n_post)

        alpha_pre  = np.median(y_pre  - beta * t_pre)
        alpha_post = np.median(y_post - beta * t_post)
        gamma = alpha_post - alpha_pre
        alpha = alpha_pre
        t_star = -(alpha + gamma) / beta

    else:
        slopes = []
        for i in range(T):
            for j in range(i+1, T):
                slopes.append((y[j] - y[i]) / (t[j] - t[i]))
        beta = np.median(slopes)
        alpha = np.median(y - beta * t)
        gamma = 0.0
        t_star = -alpha / beta

    # Bootstrap confidence interval
    n_boot = 500
    t_stars_boot = []
    rng = np.random.default_rng(42)

    for _ in range(n_boot):
        idx = rng.integers(0, T, size=T)
        t_b, y_b = t[idx], y[idx]

        if t_snap is not None:
            mask_pre  = idx < t_snap
            mask_post = idx >= t_snap
            t_pre_b, y_pre_b   = t_b[mask_pre],  y_b[mask_pre]
            t_post_b, y_post_b = t_b[mask_post], y_b[mask_post]
            if len(t_pre_b) < 2 or len(t_post_b) < 2:
                continue
            slopes_pre, slopes_post = [], []
            for i in range(len(t_pre_b)):
                for j in range(i+1, len(t_pre_b)):
                    if t_pre_b[j] != t_pre_b[i]:
                        slopes_pre.append((y_pre_b[j] - y_pre_b[i]) / (t_pre_b[j] - t_pre_b[i]))
            for i in range(len(t_post_b)):
                for j in range(i+1, len(t_post_b)):
                    if t_post_b[j] != t_post_b[i]:
                        slopes_post.append((y_post_b[j] - y_post_b[i]) / (t_post_b[j] - t_post_b[i]))
            if not slopes_pre or not slopes_post:
                continue
            b_pre  = np.median(slopes_pre)
            b_post = np.median(slopes_post)
            b = (b_pre * len(t_pre_b) + b_post * len(t_post_b)) / (len(t_pre_b) + len(t_post_b))
            a_pre  = np.median(y_pre_b  - b * t_pre_b)
            a_post = np.median(y_post_b - b * t_post_b)
            g = a_post - a_pre
            a = a_pre
            if b == 0:
                continue
            t_stars_boot.append(-(a + g) / b)

        else:
            slopes_b = []
            for i in range(T):
                for j in range(i+1, T):
                    if t_b[j] != t_b[i]:
                        slopes_b.append((y_b[j] - y_b[i]) / (t_b[j] - t_b[i]))
            if not slopes_b:
                continue
            b = np.median(slopes_b)
            a = np.median(y_b - b * t_b)
            if b == 0:
                continue
            t_stars_boot.append(-a / b)

    t_stars_boot = np.array(t_stars_boot)
    ci_lo, ci_hi = np.percentile(t_stars_boot, [2.5, 97.5]) if len(t_stars_boot) > 10 else (np.nan, np.nan)
    std_tstar = np.std(t_stars_boot) if len(t_stars_boot) > 10 else np.nan

    return {
        "t_star": t_star,
        "t_star_std": std_tstar,
        "ci_95": (ci_lo, ci_hi),
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
    }


def plot_results(stock_levels, results, t_snap=None):
    T = len(stock_levels)
    t_obs = np.arange(T)
    t_stars = [result["t_star"] for result in results]
    ci_los = [result["ci_95"][0] for result in results]
    ci_his = [result["ci_95"][1] for result in results]
    alphas = [result["alpha"] for result in results]
    betas = [result["beta"] for result in results]
    gammas = [result["gamma"] for result in results]

    # Plot all results on the same figure
    plt.figure()
    plt.plot(t_obs[20:T // 2 - 10], stock_levels[20:T//2 - 10], "o", label="Observed Stock Levels", color="blue")
    plt.plot(t_obs[T // 2 + 10:-20], stock_levels[T//2 + 10:-20], "o", color="Blue")
    plt.plot(t_obs[:20], stock_levels[:20], "o", label="First 20 Steps", color="cyan")
    plt.plot(t_obs[-20:], stock_levels[-20:], "o", label="Last 20 Steps", color="magenta")
    plt.plot(t_obs[T//2 - 10: T// 2 + 10], stock_levels[T//2 - 10: T//2 + 10], "o", label="Middle 20 Steps", color="green")
    colors = ["blue", "green", "purple", "brown", "magenta"]
    for i, (t_star, ci_lo, ci_hi, alpha, beta, gamma) in enumerate(zip(t_stars, ci_los, ci_his, alphas, betas, gammas)):
        t_end = int(max(T + 5, ci_hi + 3, t_star + 3))
        t_plot = np.linspace(0, t_end)
        color = colors[i % len(colors)]
        if t_snap is not None:
            S_plot = (t_plot >= t_snap).astype(float)
            y_plot = alpha + beta * t_plot + gamma * S_plot
        else:
            y_plot = alpha + beta * t_plot
        plt.plot(t_plot, y_plot, "-", color=color, label=f"Fitted Trend {i+1}")
        plt.axvline(t_star, color=color, linestyle="--", label=f"Predicted Stockout {i+1} (t*={t_star:.2f})")
        plt.fill_betweenx([min(stock_levels), max(stock_levels)], ci_lo, ci_hi, color=color, alpha=0.2, label=f"95% CI {i+1}")
    if t_snap is not None:
        plt.axvline(t_snap, color="orange", linestyle="--", label=f"Snap Event (t={t_snap})")
    plt.xlabel("Time")
    plt.ylabel("Stock Level")
    plt.title("Stock Level Trend and Predicted Stockout Time")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    T = 20

    # --- Snap case ---
    t_snap = 10

    stock_data = get_resource_data("../cleaned_avengers_data.csv")
    new_asgard_stock = stock_data["New Asgard"]
    resource = list(new_asgard_stock.keys())[0]
    stock_levels = np.array(new_asgard_stock[resource]["stock_level"], dtype=float)
    stock_1 = stock_levels[:T]
    stock_2 = stock_levels[-T:]
    stock_3 = stock_levels[len(stock_levels)//2 - T//2 : len(stock_levels)//2 + T//2]
    result_1_ts = fit_stockout_model_theil_sen(stock_1, t_snap=None)
    result_2_ts = fit_stockout_model_theil_sen(stock_2, t_snap=None)
    result_3_ts = fit_stockout_model_theil_sen(stock_3, t_snap=None)
    result_1 = fit_stockout_model(stock_1, t_snap=t_snap, lambda_ridge=0.5)
    result_2 = fit_stockout_model(stock_2, t_snap=t_snap, lambda_ridge=0.5)
    result_3 = fit_stockout_model(stock_3, t_snap=t_snap, lambda_ridge=0.5)
    print(f"{resource} Stock, Middle {T} Steps:")
    print(stock_3)

    # --- Snap case ---
    # print("=== With Snap ===")
    # print(f"alpha={result_snap['alpha']:.3f}  beta={result_snap['beta']:.3f}  gamma={result_snap['gamma']:.3f}")
    # print(f"Predicted stockout at t={result_snap['t_star']:.2f}  ({result_snap['t_star']-(T-1):.1f} steps from now)")
    # print(f"95% CI: ({result_snap['ci_95'][0]:.2f}, {result_snap['ci_95'][1]:.2f})")
    # plot_results(stock_snap, result_snap, t_snap=t_snap, save_path="/mnt/user-data/outputs/stockout_snap.png")

    # --- No Snap case ---
    print("\n=== Without Snap ===")
    print(f"alpha={result_3['alpha']:.3f}  beta={result_3['beta']:.3f}")
    print(f"Predicted stockout at t={result_3['t_star']:.2f}  ({result_3['t_star']-(T-1):.1f} steps from now)")
    print(f"95% CI: ({result_3['ci_95'][0]:.2f}, {result_3['ci_95'][1]:.2f})")
    plot_results(stock_levels, [result_1, result_2, result_3, result_1_ts, result_2_ts, result_3_ts], t_snap=None)