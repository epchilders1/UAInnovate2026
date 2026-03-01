from collect_data import get_resource_data, get_issue_data
import matplotlib.pyplot as plt


stock_data = get_resource_data()
issue_data = get_issue_data()

sector = list(stock_data.keys())[0]
resource = list(stock_data[sector].keys())[0]

r_stock_data = stock_data[sector][resource]
r_stock_change = [r_stock_data["stock_level"][i+1] - r_stock_data["stock_level"][i] for i in range(len(r_stock_data["stock_level"]) - 1)]

plt.figure()
plt.plot(r_stock_data["stock_level"], label="Stock Level Change")
plt.plot(r_stock_data["usage_rate_hourly"], label="Usage Rate Hourly")
plt.xlabel("Time")
plt.ylabel("Value")
plt.title(f"Stock Level Change and Usage Rate Hourly for {resource}")
plt.legend()
plt.show()