import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from clean_311_requests import classify_category, is_open_status
from analyze_requests import burden_class, percentile_rank, rate_per_10k
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

    def test_point_in_polygon(self):
        square = {
            "type": "Polygon",
            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
        }
        self.assertTrue(point_in_geometry(0, 0, square))
        self.assertFalse(point_in_geometry(2, 0, square))


if __name__ == "__main__":
    unittest.main()
