import json
import re
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

DATA_FILE = Path(__file__).parent / "vehicles.json"


class VehicleDatabase:
    def __init__(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

    def find_model_and_variant(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Inspects text to find the intended vehicle model and specific variant from the catalog.
        
        Returns:
            (canonical_model_name, canonical_variant_name)
            e.g. ("XUV700", "AX7 Luxury (AX7L)")
        """
        text_upper = text.upper()

        # 1. Thar Roxx AX7L vs XUV700 AX7 / AX7L
        if any(k in text_upper for k in ["AX7L", "AX7-L", "AX7 L", "AX7"]):
            if "ROXX" in text_upper or ("THAR" in text_upper and "ROXX" in text_upper):
                return "Thar", self._get_variant_by_keyword("THAR", "AX7L")
            return "XUV700", self._get_variant_by_keyword("XUV700", "AX7L")

        if any(k in text_upper for k in ["AX5", "AX 5", "AX-5"]):
            return "XUV700", self._get_variant_by_keyword("XUV700", "AX5")

        if re.search(r"\bMX\b", text_upper):
            return "XUV700", self._get_variant_by_keyword("XUV700", "MX")

        # 2. Scorpio-N variants
        if any(k in text_upper for k in ["Z8L", "Z8-L", "Z8 L", "Z8 LUXURY"]):
            return "Scorpio-N", self._get_variant_by_keyword("SCORPIO-N", "Z8L")

        if re.search(r"\bZ8\b", text_upper):
            return "Scorpio-N", self._get_variant_by_keyword("SCORPIO-N", "Z8")

        if re.search(r"\bZ4\b", text_upper):
            return "Scorpio-N", self._get_variant_by_keyword("SCORPIO-N", "Z4")

        # 3. Bolero Neo variants
        if any(k in text_upper for k in ["N10", "N-10", "N 10"]):
            return "Bolero Neo", self._get_variant_by_keyword("BOLERO_NEO", "N10")

        if re.search(r"\bN4\b", text_upper):
            return "Bolero Neo", self._get_variant_by_keyword("BOLERO_NEO", "N4")

        # 4. Thar variants
        if any(k in text_upper for k in ["AX OPT", "AX-OPT", "AXOPT", "AXO"]):
            return "Thar", self._get_variant_by_keyword("THAR", "AX Opt")

        if "ROXX" in text_upper:
            return "Thar", self._get_variant_by_keyword("THAR", "Roxx")

        if any(k in text_upper for k in ["HARD TOP", "LX"]):
            if "THAR" in text_upper or re.search(r"\bLX\b", text_upper):
                return "Thar", self._get_variant_by_keyword("THAR", "LX")

        # 5. Base model mentions without explicit variant
        if "XUV700" in text_upper or "XUV 700" in text_upper or "XUV" in text_upper:
            return "XUV700", None

        if "THAR" in text_upper:
            return "Thar", None

        if "SCORPIO" in text_upper:
            return "Scorpio-N", None

        if "BOLERO" in text_upper:
            return "Bolero Neo", None

        return None, None

    def _get_variant_by_keyword(self, model_key: str, keyword: str) -> str:
        """Finds full canonical variant name from vehicles.json."""
        if model_key in self.data:
            kw = keyword.upper()
            for v in self.data[model_key].get("variants", []):
                if kw in v["name"].upper():
                    return v["name"]
        return keyword

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

        # Check if the query refers to a specific variant or model
        model, _ = self.find_model_and_variant(query)
        if model:
            model_map = {
                "XUV700": "XUV700",
                "Thar": "THAR",
                "Scorpio-N": "SCORPIO-N",
                "Bolero Neo": "BOLERO_NEO",
            }
            return model_map.get(model, model.upper())

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
            if v_target in variant["name"].upper() or variant["name"].upper() in v_target:
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
