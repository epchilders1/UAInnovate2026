import numpy as np
import csv

def get_resource_data():
    with open("../historical_avengers_data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def get_stock_data():
    stock_data = get_resource_data()

    for row in stock_data:
        if row["snap_event_detected"] == "True":
            row["stock_level"] = str(2 * float(row["stock_level"]))
    return stock_data

data = get_stock_data()

with open("../cleaned_avengers_data.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
    writer.writeheader()

    for row in data:
        writer.writerow(row)