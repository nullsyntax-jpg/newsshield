# save as: src/add_test_dates.py
import json
from datetime import date, timedelta

with open("gdelt_output/final_extraction_100.json", "r") as f:
    data = json.load(f)

# Spread 100 articles across 2019-2023, one every 2 weeks
start = date(2019, 1, 7)
for i, record in enumerate(data):
    record["published_date"] = (start + timedelta(weeks=i*2)).strftime("%Y-%m-%d")

with open("gdelt_output/final_extraction_100.json", "w") as f:
    json.dump(data, f, indent=2)

print("Done — dates added to 100 records")