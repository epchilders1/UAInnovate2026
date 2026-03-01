from collect_data import get_resource_data
import matplotlib.pyplot as plt
import numpy as np


cleaned_stock_data = get_resource_data("../avengers_data_with_snap.csv")

for sector in cleaned_stock_data.keys():
    for resource in cleaned_stock_data[sector].keys():
        cleaned_levels = cleaned_stock_data[sector][resource]["stock_level"]
        plt.figure(figsize=(12, 6))
        plt.plot(cleaned_levels, label="Cleaned Stock Level")
        plt.title(f"Stock Levels for {resource} in {sector}")
        plt.xlabel("Time")
        plt.ylabel("Stock Level")
        plt.legend()
        plt.show()