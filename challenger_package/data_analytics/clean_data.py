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

data = get_stock_data()

with open("../cleaned_avengers_data.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
    writer.writeheader()

    for row in data:
        writer.writerow(row)