import json
from typing import Optional, Dict, Any, List
from pathlib import Path

DATA_FILE = Path(__file__).parent / "vehicles.json"


class VehicleDatabase:
    def __init__(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

    def normalize_name(self, query: str) -> Optional[str]:
        q = query.upper().replace("-", "").replace(" ", "").replace("_", "")
        if "XUV" in q and "700" in q:
            return "XUV700"
        if "THAR" in q:
            return "THAR"
        if "SCORPIO" in q:
            return "SCORPIO-N"
        if "BOLERO" in q:
            return "BOLERO_NEO"
        return None

    def get_vehicle_summary(self, model_query: str) -> Optional[Dict[str, Any]]:
        key = self.normalize_name(model_query)
        if not key or key not in self.data:
            return None
        return self.data[key]

    def get_variant_details(self, model_query: str, variant_name: str) -> Optional[Dict[str, Any]]:
        vehicle = self.get_vehicle_summary(model_query)
        if not vehicle:
            return None
        v_target = variant_name.upper().strip()
        for variant in vehicle["variants"]:
            if v_target in variant["name"].upper():
                return variant
        return None

    def list_all_models(self) -> List[Dict[str, str]]:
        return [
            {
                "key": k,
                "name": v["model_name"],
                "price_range": v["price_range"],
                "segment": v["segment"],
            }
            for k, v in self.data.items()
        ]


vehicle_db = VehicleDatabase()
