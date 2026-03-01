import json

def get_resource_data(filename="../historical_avengers_data.csv"):
    with open(filename, "r") as file:
        lines = file.readlines()[1:]

    sector_to_resource = {}

    for line in lines:
        timestamp,sector_id,resource_type,stock_level,usage_rate_hourly,snap_event_detected = line.strip().split(",")

        if sector_id not in sector_to_resource.keys():
            sector_to_resource[sector_id] = {}
            sector_to_resource[sector_id][resource_type] = {
                "timestamp": [],
                "stock_level": [],
                "usage_rate_hourly": [],
                "snap_event_detected": []
            }

        # if len(sector_to_resource[sector_id][resource_type]["timestamp"]) == 0 or timestamp != sector_to_resource[sector_id][resource_type]["timestamp"][-1]:
        sector_to_resource[sector_id][resource_type]["timestamp"].append(timestamp)
        sector_to_resource[sector_id][resource_type]["stock_level"].append(float(stock_level))
        sector_to_resource[sector_id][resource_type]["usage_rate_hourly"].append(float(usage_rate_hourly))
        sector_to_resource[sector_id][resource_type]["snap_event_detected"].append(snap_event_detected == "True")
    return sector_to_resource

def get_issue_data():
    with open("../field_intel_reports.json", "r") as file:
        return json.load(file)