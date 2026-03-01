import numpy as np
from typing import Optional, Dict, Any
import datetime

class RegressionResult:
    async def __init__(self, alpha, beta, gamma, t_star, t_star_std, ci_95):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.t_star = t_star
        self.t_star_std = t_star_std
        self.ci_95 = ci_95

    async def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "t_star": self.t_star,
            "t_star_std": self.t_star_std,
            "ci_95": self.ci_95,
        }

class Regression:
    async def __init__(self, stock_levels: np.ndarray, t_0: datetime.datetime, t_snap: Optional[int] = None, lambda_ridge: float = 1.0):
        self.stock_levels = np.array(stock_levels, dtype=float)
        self.T = len(stock_levels)
        self.t_0 = t_0
        self.t_snap = t_snap
        self.lambda_ridge = lambda_ridge
        self.result = None

    async def fit(self) -> RegressionResult:
        t = np.arange(self.T, dtype=float)
        y = self.stock_levels

        if self.t_snap is not None:
            t_pre, y_pre = t[t < self.t_snap], y[t < self.t_snap]
            t_post, y_post = t[t >= self.t_snap], y[t >= self.t_snap]

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
            for i in range(self.T):
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

            if self.t_snap is not None:
                mask_pre  = idx < self.t_snap
                mask_post = idx >= self.t_snap
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

        self.result = RegressionResult(alpha, beta, gamma, t_star, std_tstar, (ci_lo, ci_hi))
        return self.result

    @staticmethod
    async def _compute_weights(T, t_snap=None):
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

    async def get_result_dict(self) -> Optional[Dict[str, Any]]:
        if self.result:
            return self.result.to_dict()
        return None
    
    async def get_line(self) -> Optional[Dict[str, Any]]:
        if not self.result:
            return None
        
        t_star = self.result.t_star
        ci_lo, ci_hi = self.result.ci_95
        t_end = int(max(self.T + 5, ci_hi + 3 if not np.isnan(ci_hi) else 0, t_star + 3 if not np.isnan(t_star) else 0))
        t_plot = np.linspace(0, t_end)
        timestamps = [self.t_0 + datetime.timedelta(minutes=12 * int(i)) for i in t_plot]

        # Snap logic: if t_snap is set, add gamma after snap
        if self.t_snap is not None:
            S_plot = (t_plot < self.t_snap).astype(float)
            line = self.result.alpha + self.result.beta * t_plot + self.result.gamma * S_plot
        else:
            line = self.result.alpha + self.result.beta * t_plot
        
        return {
            "timestamps": timestamps,
            "line": line.tolist()
        }
    
    async def get_confidence_interval(self) -> Optional[Dict[str, Any]]:
        if not self.result:
            return None
        
        t_star = self.result.t_star
        ci_lo, ci_hi = self.result.ci_95

        if t_star <= 0:
            return {
                "OK": False
            }
        else:
            return{
                "OK": True,
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
                "t_star": t_star
            }