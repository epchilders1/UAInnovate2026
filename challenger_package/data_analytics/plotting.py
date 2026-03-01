from collect_data import get_resource_data
from regression import Regression
import matplotlib.pyplot as plt
import numpy as np
import datetime

stock_data = get_resource_data("../avengers_data_with_snap.csv")

T_window = 20

fig, axes = plt.subplots(len(stock_data), 1, figsize=(14, 5 * len(stock_data)), sharex=False)
if len(stock_data) == 1:
    axes = [axes]

for ax, (sector, resources) in zip(axes, stock_data.items()):
    for resource_name, resource_data in resources.items():
        stock_levels = np.array(resource_data["stock_level"], dtype=float)
        timestamps   = resource_data["timestamp"]  # list of ISO strings

        t_snap = None
        for i in range(len(stock_levels) - 1, len(stock_levels) - 2 * T_window, -1):
            print(resource_data["snap_event_detected"][i])
            if resource_data["snap_event_detected"][i]:
                t_snap = T_window - 1 - (len(stock_levels) - 1 - i)
                break
        print(f't_snap = {t_snap}')

        # Parse t_0 as the timestamp of the first point in the window
        t_0 = datetime.datetime.fromisoformat(timestamps[-T_window])

        # Fit on last 20 points
        window = stock_levels[-T_window:]
        reg = Regression(stock_levels=window, t_0=t_0, t_snap=t_snap)
        reg.fit()

        # Full series
        t_full = np.arange(len(stock_levels))
        ax.plot(t_full, stock_levels, color="#4fc3f7", linewidth=0.8,
                alpha=0.6, label=f"{resource_name} stock")

        # Highlight the last 20 points
        ax.scatter(t_full[-T_window:], window, color="#f48fb1", s=20, zorder=5,
                   label="Fitting window (last 20)")

        # Fitted line — offset to global time axis
        line_data = reg.get_line()
        if line_data:
            t_line = np.linspace(len(stock_levels) - T_window,
                                 len(stock_levels) - T_window + len(line_data["data"]) - 1,
                                 len(line_data["data"]))
            ax.plot(t_line, line_data["data"], color="#ffd54f", linewidth=2,
                    label="Fitted trend")

        # Confidence interval and stockout marker
        ci = reg.get_confidence_interval()
        if ci and ci["OK"]:
            t_star_global = ci["t_star"] + (len(stock_levels) - T_window)
            ci_lo_global  = (ci["ci_lo"] or ci["t_star"]) + (len(stock_levels) - T_window)
            ci_hi_global  = (ci["ci_hi"] or ci["t_star"]) + (len(stock_levels) - T_window)

            ax.axvline(t_star_global, color="#ff6b6b", linewidth=2, linestyle="--",
                       label=f"Predicted stockout t*={t_star_global:.1f}")
            ax.axvspan(ci_lo_global, ci_hi_global, alpha=0.15, color="#ff6b6b",
                       label=f"95% CI [{ci_lo_global:.1f}, {ci_hi_global:.1f}]")
            ax.scatter([t_star_global], [0], color="#ff6b6b", s=100, zorder=6, marker="*")
        else:
            ax.set_title(f"{sector} — {resource_name} (no stockout predicted)",
                         fontsize=11)

        ax.axhline(0, color="#ffffff40", linewidth=1)
        ax.axvline(len(stock_levels) - T_window, color="#ffffff30",
                   linewidth=1, linestyle=":", label="Window start")
        ax.set_title(f"{sector} — {resource_name}", fontsize=12)
        ax.set_xlabel("Time step")
        ax.set_ylabel("Stock Level")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

plt.tight_layout()
plt.show()