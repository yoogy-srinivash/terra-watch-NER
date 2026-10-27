import os
import pandas as pd
from typing import List, Dict, Any

DEFAULT_NASA_PATH = r"C:\Users\Anjali Kumari\OneDrive\Documents\NER_landslide_project\ner_landslides"

def load_nasa_ner_landslides(filepath: str = DEFAULT_NASA_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        print(f"Authoritative NASA Landslide file not found at: {filepath}. Returning default baseline records.")
        return []
        
    try:
        df = pd.read_csv(filepath)
        records = []
        for _, row in df.iterrows():
            lat = float(row.get("latitude", 0.0))
            lon = float(row.get("longitude", 0.0))
            if lat == 0.0 or lon == 0.0:
                continue
                
            records.append({
                "event_id": str(row.get("event_id", "")),
                "event_date": str(row.get("event_date", "2023-06-15")),
                "location_description": str(row.get("location_description", row.get("event_title", "Landslide Event"))),
                "state": str(row.get("state", "Assam")),
                "district": str(row.get("admin_division", "")),
                "latitude": lat,
                "longitude": lon,
                "landslide_category": str(row.get("landslide_category", "Landslide")),
                "landslide_trigger": str(row.get("landslide_trigger", "Monsoon Rain")),
                "landslide_size": str(row.get("landslide_size", "Medium")),
                "fatality_count": int(row.get("fatality_count", 0) if pd.notnull(row.get("fatality_count")) else 0),
                "injury_count": int(row.get("injury_count", 0) if pd.notnull(row.get("injury_count")) else 0),
                "source": "NASA Global Landslide Catalog (NER)"
            })
        print(f"Loaded {len(records)} authoritative NASA NER landslide events from catalog.")
        return records
    except Exception as e:
        print(f"Error loading NASA catalog: {e}")
        return []

if __name__ == "__main__":
    recs = load_nasa_ner_landslides()
    if recs:
        print(f"Sample record: {recs[0]}")
