import numpy as np
import warnings
import matplotlib.pyplot as plt

def generate_stock_data(T=20, t_snap=10, seed=42):
    rng = np.random.default_rng(seed)
    pre_snap = np.zeros(t_snap)
    pre_snap[0] = 100
    for i in range(1, t_snap):
        pre_snap[i] = pre_snap[i-1] - 2 + rng.normal(0, 0.5 * np.sqrt(i))
    snap_level = pre_snap[-1] / 2
    post_snap = np.zeros(T - t_snap)
    post_snap[0] = snap_level
    for i in range(1, T - t_snap):
        post_snap[i] = post_snap[i-1] - 2 + rng.normal(0, 0.5 * np.sqrt(i))
    return np.concatenate([pre_snap, post_snap])


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
        P = lambda_ridge * np.diag([1.0, 1.0, 0.0])
    else:
        X = np.column_stack([np.ones(T), t])
        P = lambda_ridge * np.diag([1.0, 1.0])

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


def plot_results(stock_levels, result, t_snap=None, save_path="stockout_plot.png"):
    T = len(stock_levels)
    t_obs = np.arange(T)
    t_star = result["t_star"]
    ci_lo, ci_hi = result["ci_95"]
    alpha, beta, gamma = result["alpha"], result["beta"], result["gamma"]
    cov_theta = result["cov_theta"]
    weights = result["weights"]

    t_end = int(max(T + 5, ci_hi + 3, t_star + 3))
    t_plot = np.linspace(0, t_end, 500)

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")
    ax.grid(color="#ffffff15", linestyle="--", linewidth=0.5, zorder=0)

    # Extrapolation CI band
    t_extrap = t_plot[t_plot >= T - 1]
    if t_snap is not None:
        X_extrap = np.column_stack([np.ones_like(t_extrap), t_extrap, np.ones_like(t_extrap)])
        y_extrap = alpha + beta * t_extrap + gamma
    else:
        X_extrap = np.column_stack([np.ones_like(t_extrap), t_extrap])
        y_extrap = alpha + beta * t_extrap

    pointwise_var = np.array([x @ cov_theta @ x for x in X_extrap])
    pointwise_std = np.sqrt(np.maximum(pointwise_var, 0))
    ax.fill_between(t_extrap, y_extrap - 1.96*pointwise_std, y_extrap + 1.96*pointwise_std,
                    alpha=0.15, color="#4fc3f7", label="95% prediction band")

    # Fitted lines
    if t_snap is not None:
        t_pre = t_plot[t_plot < t_snap]
        ax.plot(t_pre, alpha + beta*t_pre, color="#4fc3f7", linewidth=1.5, linestyle="--", alpha=0.4)
        t_post = t_plot[t_plot >= t_snap]
        ax.plot(t_post, alpha + beta*t_post + gamma, color="#4fc3f7", linewidth=2, label="Fitted trend (post-snap)")
    else:
        ax.plot(t_plot, alpha + beta*t_plot, color="#4fc3f7", linewidth=2, label="Fitted trend")

    # Data points sized by weight
    sizes = 40 + 220 * weights / weights.max()
    if t_snap is not None:
        pre_mask = t_obs < t_snap
        post_mask = t_obs >= t_snap
        ax.scatter(t_obs[pre_mask], stock_levels[pre_mask], s=sizes[pre_mask],
                   color="#90caf9", zorder=5, label="Pre-snap", edgecolors="#ffffff25", linewidths=0.5)
        ax.scatter(t_obs[post_mask], stock_levels[post_mask], s=sizes[post_mask],
                   color="#f48fb1", zorder=5, label="Post-snap", edgecolors="#ffffff25", linewidths=0.5)
        ax.axvline(t_snap, color="#ff6b6b", linewidth=1.5, linestyle=":", alpha=0.8,
                   label=f"Thanos snap (t={t_snap})")
    else:
        ax.scatter(t_obs, stock_levels, s=sizes, color="#90caf9", zorder=5,
                   label="Observations", edgecolors="#ffffff25", linewidths=0.5)

    # Zero line
    ax.axhline(0, color="#ffffff35", linewidth=1)

    # Stockout prediction
    ax.axvline(t_star, color="#ffd54f", linewidth=2, alpha=0.9,
               label=f"Predicted stockout t={t_star:.1f}")
    ax.axvspan(ci_lo, ci_hi, alpha=0.08, color="#ffd54f",
               label=f"95% CI [{ci_lo:.1f}, {ci_hi:.1f}]")
    ax.scatter([t_star], [0], color="#ffd54f", s=140, zorder=6, marker="*")

    # "Now" line
    ax.axvline(T - 1, color="#ffffff25", linewidth=1, linestyle="--")
    ylims = ax.get_ylim()
    ax.text(T - 0.7, ylims[1] * 0.97, "now", color="#ffffff50", fontsize=8)

    # Annotation
    steps_out = t_star - (T - 1)
    snap_line = f"γ (level shift) = {gamma:.2f}\n" if t_snap is not None else ""
    info = (
        f"α (intercept) = {alpha:.3f}\n"
        f"β (drift/step) = {beta:.3f}\n"
        f"{snap_line}"
        f"σ² = {result['sigma2']:.3f}\n"
        f"Stockout in ~{steps_out:.1f} steps"
    )
    ax.text(0.02, 0.05, info, transform=ax.transAxes, fontsize=9,
            color="#ffffffcc", verticalalignment="bottom", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#1e2130",
                      edgecolor="#ffffff20", alpha=0.85))

    ax.set_xlabel("Time step", color="#ffffffcc", fontsize=11)
    ax.set_ylabel("Stock Level", color="#ffffffcc", fontsize=11)
    title = "Stock Level Ridge Regression — With Snap" if t_snap is not None else "Stock Level Ridge Regression — No Snap"
    ax.set_title(title, color="#ffffff", fontsize=13, pad=12)
    ax.tick_params(colors="#ffffffaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#ffffff15")
    ax.legend(facecolor="#1e2130", edgecolor="#ffffff20", labelcolor="#ffffffcc", fontsize=8.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {save_path}")


if __name__ == "__main__":
    T = 20

    # --- Snap case ---
    t_snap = 10
    stock_snap = generate_stock_data(T=T, t_snap=t_snap, seed=7)
    result_snap = fit_stockout_model(stock_snap, t_snap=t_snap, lambda_ridge=0.5)

    print("=== With Snap ===")
    print(f"alpha={result_snap['alpha']:.3f}  beta={result_snap['beta']:.3f}  gamma={result_snap['gamma']:.3f}")
    print(f"Predicted stockout at t={result_snap['t_star']:.2f}  ({result_snap['t_star']-(T-1):.1f} steps from now)")
    print(f"95% CI: ({result_snap['ci_95'][0]:.2f}, {result_snap['ci_95'][1]:.2f})")
    plot_results(stock_snap, result_snap, t_snap=t_snap, save_path="/mnt/user-data/outputs/stockout_snap.png")

    # --- No snap case ---
    rng = np.random.default_rng(42)
    stock_no_snap = np.zeros(T)
    stock_no_snap[0] = 100
    for i in range(1, T):
        stock_no_snap[i] = stock_no_snap[i-1] - 2 + rng.normal(0, 0.5 * np.sqrt(i))
    result_no_snap = fit_stockout_model(stock_no_snap, t_snap=None, lambda_ridge=0.5)

    print("\n=== Without Snap ===")
    print(f"alpha={result_no_snap['alpha']:.3f}  beta={result_no_snap['beta']:.3f}")
    print(f"Predicted stockout at t={result_no_snap['t_star']:.2f}  ({result_no_snap['t_star']-(T-1):.1f} steps from now)")
    print(f"95% CI: ({result_no_snap['ci_95'][0]:.2f}, {result_no_snap['ci_95'][1]:.2f})")
    plot_results(stock_no_snap, result_no_snap, t_snap=None, save_path="/mnt/user-data/outputs/stockout_nosnap.png")