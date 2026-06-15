import sys
import unittest
from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from clean_311_requests import classify_category, is_open_status
from analyze_requests import burden_class, json_safe, percentile_rank, rate_per_10k
from project_config import SCORE_WEIGHTS
from spatial_utils import point_in_geometry


class CoreLogicTests(unittest.TestCase):
    def test_category_classification_prioritizes_sewer_before_water(self):
        self.assertEqual(classify_category("Sewer Wastewater"), "Sewer / Wastewater")
        self.assertEqual(classify_category("Water Leak"), "Water")
        self.assertEqual(classify_category("Traffic Signal Maintenance"), "Traffic Signals / Lighting")

    def test_open_status_logic(self):
        self.assertTrue(is_open_status("In Progress", "Active", None))
        self.assertFalse(is_open_status("Service Completed", "Resolved", "2025-06-01"))
        self.assertFalse(is_open_status("Merged", "Cancelled", None))

    def test_burden_class_thresholds(self):
        self.assertEqual(burden_class(12), "Low")
        self.assertEqual(burden_class(30), "Medium")
        self.assertEqual(burden_class(60), "High")
        self.assertEqual(burden_class(80), "Very High")

    def test_configured_score_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(SCORE_WEIGHTS.values()), 1.0)

    def test_rate_per_10k_handles_missing_denominator(self):
        rates = rate_per_10k(numerator=pd.Series([5, 10]), denominator=pd.Series([1000, 0]))
        self.assertAlmostEqual(rates[0], 50.0)
        self.assertTrue(np.isnan(rates[1]))

    def test_percentile_rank_zeroes_flat_series(self):
        ranked = percentile_rank(pd.Series([3, 3, 3]))
        self.assertEqual(ranked.tolist(), [0, 0, 0])

    def test_json_safe_replaces_nan(self):
        cleaned = json_safe({"value": np.nan, "items": [np.float64(2.5), np.nan]})
        self.assertEqual(cleaned, {"value": None, "items": [2.5, None]})

    def test_point_in_polygon(self):
        square = {
            "type": "Polygon",
            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
        }
        self.assertTrue(point_in_geometry(0, 0, square))
        self.assertFalse(point_in_geometry(2, 0, square))

    def test_required_static_gis_outputs_exist(self):
        required = [
            ROOT / "deliverables" / "map_plates" / "houston_311_service_burden_map_plate.png",
            ROOT / "deliverables" / "map_plates" / "houston_311_service_burden_map_plate_grayscale.png",
            ROOT / "deliverables" / "map_plates" / "houston_311_service_burden_map_plate_thumbnail.png",
            ROOT / "deliverables" / "map_plates" / "score_component_small_multiples.png",
            ROOT / "deliverables" / "map_plates" / "non_solid_waste_screening_map_plate.png",
            ROOT / "deliverables" / "map_plates" / "category_balanced_density_map_plate.png",
            ROOT / "deliverables" / "map_plates" / "district_assignment_qa_map_plate.png",
            ROOT / "deliverables" / "houston_311_static_gis_atlas.pdf",
            ROOT / "outputs" / "tables" / "score_components.csv",
            ROOT / "outputs" / "tables" / "score_sensitivity_rankings.csv",
            ROOT / "outputs" / "tables" / "source_spatial_assignment_matrix.csv",
            ROOT / "outputs" / "maps" / "request_density_component.png",
            ROOT / "outputs" / "maps" / "non_solid_waste_screening_score.png",
            ROOT / "outputs" / "maps" / "category_balanced_density_score.png",
            ROOT / "outputs" / "maps" / "district_assignment_qa_flags.png",
            ROOT / "outputs" / "gis" / "council_district_screening_index.geojson",
            ROOT / "outputs" / "gis" / "district_assignment_qa_flags.geojson",
            ROOT / "outputs" / "gis" / "repeat_location_clusters.geojson",
        ]
        missing = [str(path) for path in required if not path.exists()]
        self.assertEqual(missing, [])

    def test_score_component_schema(self):
        path = ROOT / "outputs" / "tables" / "score_components.csv"
        components = pd.read_csv(path)
        expected = {
            "council_district",
            "component",
            "component_label",
            "weight",
            "percentile",
            "weighted_points",
            "service_burden_score",
            "service_burden_class",
        }
        self.assertTrue(expected.issubset(set(components.columns)))
        self.assertEqual(len(components), 66)

    def test_sensitivity_and_gis_outputs_schema(self):
        sensitivity = pd.read_csv(ROOT / "outputs" / "tables" / "score_sensitivity_rankings.csv")
        self.assertTrue({"scenario", "council_district", "rank", "score"}.issubset(sensitivity.columns))
        self.assertIn("non_solid_waste_current_weights", set(sensitivity["scenario"]))

        gis_path = ROOT / "outputs" / "gis" / "council_district_screening_index.geojson"
        geojson = json.loads(gis_path.read_text(encoding="utf-8"))
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertGreaterEqual(len(geojson["features"]), 11)
        properties = geojson["features"][0]["properties"]
        self.assertIn("baseline_service_burden_score", properties)


if __name__ == "__main__":
    unittest.main()
