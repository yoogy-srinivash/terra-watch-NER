import json
import os

from risk_report import generate_risk_report


with open(os.path.join(os.path.dirname(__file__), "input.json"), "r") as file:
    data = json.load(file)


report = generate_risk_report(
    risk_score=data["risk_score"],
    rainfall=data["features"]["rainfall"],
    soil_moisture=data["features"]["soil_moisture"],
    slope=data["features"]["slope"]
)


report["location"] = data["location"]


with open(os.path.join(os.path.dirname(__file__), "output.json"), "w") as file:
    json.dump(report, file, indent=4)


print("Risk report generated successfully.")
print(report)