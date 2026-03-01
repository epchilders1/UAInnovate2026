import numpy as np
import csv

def get_resource_data():
    with open("../historical_avengers_data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def get_stock_data():
    import datetime
    stock_data = get_resource_data()
    if not stock_data:
        return stock_data

    # Set group size to 5 (number of resources per timestamp)
    group_size = 5
    first_timestamp = stock_data[0]["timestamp"]
    start_dt = datetime.datetime.fromisoformat(first_timestamp)

    for i, row in enumerate(stock_data):
        group_idx = i // group_size
        new_dt = start_dt + datetime.timedelta(minutes=12 * group_idx)
        row["timestamp"] = new_dt.strftime("%Y-%m-%dT%H:%M:%S")
        if row["snap_event_detected"] == "True":
            row["stock_level"] = str(2 * float(row["stock_level"]))
    return stock_data

N = 1000 # number of points to keep
M = 10 # number of points to generate after snap

data = get_stock_data()

data_to_write = data[:(N+1)*5]  # Keep original data for first N timestamps (5 resources per timestamp)

last_timestamp = data_to_write[-1]["timestamp"]
last_stock_levels = [float(row["stock_level"]) for row in data_to_write[-5:]]  # Last 5 entries correspond to the last timestamp

# === Trend Estimates ===
beta0 = 2505.5774286991327
beta1 = -1.0029537890727949

# === Variance Estimates ===
alpha = 2.3478426304294047
sigma = 0.116316436241579

last_stock_levels


with open("../cleaned_avengers_data.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
    writer.writeheader()

    for row in data[:N*5]:
        writer.writerow(row)
    for i in range(N*5, min(N*5 + M*5, len(data))):
        row = data[i].copy()
        row["timestamp"] = data[i]["timestamp"]  # Keep original timestamp
        writer.writerow(row)