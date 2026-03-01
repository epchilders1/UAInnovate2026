from collect_data import get_resource_data
import matplotlib.pyplot as plt
import numpy as np


original_stock_data = get_resource_data()
cleaned_stock_data = get_resource_data("../cleaned_avengers_data.csv")

for sector in original_stock_data.keys():
    for resource in original_stock_data[sector].keys():
        original_levels = original_stock_data[sector][resource]["stock_level"]
        cleaned_levels = cleaned_stock_data[sector][resource]["stock_level"]
        plt.figure(figsize=(12, 6))
        plt.plot(original_levels, label="Original Stock Level", alpha=0.7)
        plt.plot(cleaned_levels, label="Cleaned Stock Level", alpha=0.7)
        plt.title(f"Stock Levels for {resource} in {sector}")
        plt.xlabel("Time")
        plt.ylabel("Stock Level")
        plt.legend()
        plt.show()