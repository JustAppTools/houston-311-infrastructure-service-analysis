import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from clean_311_requests import classify_category, is_open_status
from analyze_requests import burden_class
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

    def test_point_in_polygon(self):
        square = {
            "type": "Polygon",
            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
        }
        self.assertTrue(point_in_geometry(0, 0, square))
        self.assertFalse(point_in_geometry(2, 0, square))


if __name__ == "__main__":
    unittest.main()
