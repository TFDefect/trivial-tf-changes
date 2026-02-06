
import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from scripts.process.delta_metrics import DeltaMetrics

class TestDeltaMetrics(unittest.TestCase):
    def test_delta_calculation(self):
        # Setup
        block_after = {
            "block_identifiers": "foo",
            "numAttrs": 5, 
            "complexity": 10,
            "is_new": "yes" # non-numeric, should be ignored
        }
        block_before = {
            "block_identifiers": "foo",
            "numAttrs": 3,
            "complexity": 10
        }
        
        # Act
        delta = DeltaMetrics(block_after, block_before)
        results = delta.compute_delta_metrics()
        
        # Assert
        self.assertEqual(results.get("numAttrs_delta"), 2)     # 5 - 3 = 2
        self.assertEqual(results.get("complexity_delta"), 0)   # 10 - 10 = 0
        self.assertNotIn("is_new_delta", results)              # Ignored string
        self.assertNotIn("start_block_delta", results)         # Filtered key (by default implementation)

    def test_new_block(self):
        # Setup: No before block
        block_after = {"numAttrs": 5}
        block_before = None
        
        # Act
        delta = DeltaMetrics(block_after, block_before)
        results = delta.compute_delta_metrics()
        
        # Assert
        # Assuming logic: if before is None, treat as 0.
        self.assertEqual(results.get("numAttrs_delta"), 5) # 5 - 0 = 5

if __name__ == '__main__':
    unittest.main()
