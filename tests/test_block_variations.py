
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from scripts.impacted_block_detection import ImpactedBlocks

class TestBlockVariations(unittest.TestCase):
    def setUp(self):
        # Create a mock Modification object from pydriller
        self.mock_mod = MagicMock()
        self.mock_mod.source_code = "dummy"
        self.mock_mod.source_code_before = "dummy"
        self.mock_mod.filename = "main.tf"
        
    def create_impacted_blocks(self, blocks_after, blocks_before, added_lines, removed_lines):
        """
        Helper to create an ImpactedBlocks instance with mocked internal data.
        We strictly bypass the actual parsing (_get_blocks) by subclassing or patching.
        Here we instantiate, but then immediately overwrite the attributes.
        BUT: __init__ calls _get_blocks. We must mock it on the class or instance *before* init, 
        or patch it.
        """
        # Patch _get_blocks to return empty lists initially so __init__ doesn't explode
        with unittest.mock.patch('scripts.impacted_block_detection.ImpactedBlocks._get_blocks', return_value=[]):
            ib = ImpactedBlocks(self.mock_mod)
        
        # Inject mocked data
        ib.blocks_after_change = blocks_after
        ib.blocks_before_change = blocks_before
        ib.added_lines = added_lines
        ib.removed_lines = removed_lines
        
        # Reset statuses based on injected data
        ib.status_after_change = 200 if blocks_after else 404
        ib.status_before_change = 200 if blocks_before else 404
        
        return ib

    def test_resource_change(self):
        """
        Test modification of a standard resource block.
        """
        # Scenario: google_compute_instance "default" changed at line 15
        block_after = {
            "block_identifiers": "resource.google_compute_instance.default",
            "block_name": "resource",
            "start_block": 10,
            "end_block": 20,
            "numAttrs": 5
        }
        # Before state (same identifier, maybe different lines if content shifted)
        block_before = {
            "block_identifiers": "resource.google_compute_instance.default",
            "block_name": "resource",
            "start_block": 10,
            "end_block": 20,
            "numAttrs": 5
        }
        
        # Line 15 modified (added)
        blocks = self.create_impacted_blocks([block_after], [block_before], [15], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "resource.google_compute_instance.default")
        
        # Verify get_block finds the pair
        pair = blocks.get_block(impacted[0], [block_before])
        self.assertIsNotNone(pair)
        self.assertEqual(pair["block_identifiers"], block_before["block_identifiers"])

    def test_module_change(self):
        """
        Test modification of a module block.
        """
        # Scenario: module "kubernetes" changed
        block_after = {
            "block_identifiers": "module.kubernetes",
            "block_name": "module",
            "start_block": 30,
            "end_block": 40,
            "numAttrs": 3
        }
        block_before = {
            "block_identifiers": "module.kubernetes",
            "block_name": "module",
            "start_block": 25, # shifted
            "end_block": 35,
            "numAttrs": 3
        }
        
        # Line 32 added (inside 30-40)
        blocks = self.create_impacted_blocks([block_after], [block_before], [32], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "module.kubernetes")
        
        # Verify get_block handles the shift (identifiers match)
        pair = blocks.get_block(impacted[0], [block_before])
        self.assertEqual(pair["start_block"], 25)

    def test_data_source_change(self):
        """
        Test modification of a data source.
        """
        # Scenario: data "google_compute_image" "my_image"
        block_after = {
            "block_identifiers": "data.google_compute_image.my_image",
            "block_name": "data",
            "start_block": 5,
            "end_block": 8,
            "numAttrs": 2
        }
        block_before = {
             "block_identifiers": "data.google_compute_image.my_image",
             "block_name": "data",
             "start_block": 5,
             "end_block": 8,
             "numAttrs": 2
        }
        
        blocks = self.create_impacted_blocks([block_after], [block_before], [6], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "data.google_compute_image.my_image")

    def test_provider_change(self):
        """
        Test modification of a provider block.
        """
        block_after = {
            "block_identifiers": "provider.google",
            "block_name": "provider",
            "start_block": 1,
            "end_block": 4,
            "numAttrs": 1
        }
        block_before = {
            "block_identifiers": "provider.google",
            "block_name": "provider",
            "start_block": 1,
            "end_block": 4,
            "numAttrs": 1
        }
        
        blocks = self.create_impacted_blocks([block_after], [block_before], [2], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)

    def test_multiple_blocks(self):
        """
        Test file with multiple blocks where only one is modified.
        """
        b1_after = {"block_identifiers": "b1", "start_block": 10, "end_block": 20}
        b2_after = {"block_identifiers": "b2", "start_block": 30, "end_block": 40}
        
        # Change only in b2 (line 35)
        blocks = self.create_impacted_blocks([b1_after, b2_after], [b1_after, b2_after], [35], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "b2")

    def test_change_outside_blocks(self):
        """
        Test change strictly outside any known block (e.g., top-level comment).
        """
        b1 = {"block_identifiers": "b1", "start_block": 10, "end_block": 20}
        # Change at line 5 (before block)
        blocks = self.create_impacted_blocks([b1], [b1], [5], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        
        self.assertEqual(len(impacted), 0, "Top level change (outside block) should not identify block as impacted")

    def test_block_renamed(self):
        """
        Test when a block identifier changes (e.g., resource renamed).
        The before and after have different identifiers.
        """
        # Before: resource "aws_instance" "old_name"
        block_before = {
            "block_identifiers": "resource.aws_instance.old_name",
            "start_block": 10,
            "end_block": 20,
            "numAttrs": 5
        }
        # After: resource "aws_instance" "new_name"
        block_after = {
            "block_identifiers": "resource.aws_instance.new_name",
            "start_block": 10,
            "end_block": 20,
            "numAttrs": 5
        }
        
        # Line 15 changed
        blocks = self.create_impacted_blocks([block_after], [block_before], [15], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        # Should identify the new block
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "resource.aws_instance.new_name")
        
        # get_block should NOT find a match (different identifiers)
        pair = blocks.get_block(impacted[0], [block_before])
        self.assertIsNone(pair, "Renamed block should not match by identifier")

    def test_block_deleted(self):
        """
        Test when a block is completely removed.
        """
        # Before: had a block
        block_before = {
            "block_identifiers": "resource.to_delete",
            "start_block": 10,
            "end_block": 15,
            "numAttrs": 3
        }
        # After: block is gone
        # Lines 10-15 removed
        blocks = self.create_impacted_blocks([], [block_before], [], [11, 12, 13])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        # The completeness logic checks if removed lines fall in before blocks
        # Since all attrs removed (cpt == numAttrs), it should NOT add to impacted
        # Based on line 139-140: if cpt == numAttrs: pass
        self.assertEqual(len(impacted), 0, "Fully deleted block should not be in impacted list")

    def test_block_added(self):
        """
        Test when a new block is added (no before version).
        """
        # After: new block
        block_after = {
            "block_identifiers": "resource.new_resource",
            "start_block": 25,
            "end_block": 30,
            "numAttrs": 2
        }
        # Before: nothing
        # Line 27 added
        blocks = self.create_impacted_blocks([block_after], [], [27], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "resource.new_resource")
        
        # get_block should return None (no before version)
        pair = blocks.get_block(impacted[0], [])
        self.assertIsNone(pair)

    def test_line_shift_same_block(self):
        """
        Test when block content shifts (e.g., due to insertions above).
        Same identifier, different line ranges.
        """
        block_before = {
            "block_identifiers": "module.app",
            "start_block": 50,
            "end_block": 60,
            "numAttrs": 4
        }
        # After: shifted down by 5 lines
        block_after = {
            "block_identifiers": "module.app",
            "start_block": 55,
            "end_block": 65,
            "numAttrs": 4
        }
        
        # Line 58 modified (inside new range)
        blocks = self.create_impacted_blocks([block_after], [block_before], [58], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        
        # get_block should find the match despite line shift
        pair = blocks.get_block(impacted[0], [block_before])
        self.assertIsNotNone(pair)
        self.assertEqual(pair["start_block"], 50, "Should match to before block at line 50")

    def test_partial_deletion(self):
        """
        Test when some attributes are removed but block still exists.
        """
        block_before = {
            "block_identifiers": "resource.partial",
            "start_block": 70,
            "end_block": 80,
            "numAttrs": 5
        }
        block_after = {
            "block_identifiers": "resource.partial",
            "start_block": 70,
            "end_block": 78,  # Smaller
            "numAttrs": 3  # Fewer attrs
        }
        
        # 2 lines removed (75, 76)
        blocks = self.create_impacted_blocks([block_after], [block_before], [], [75, 76])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        # Completeness logic: cpt=2, numAttrs=5, so 5 > 2 >= 1 -> should add target_block
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "resource.partial")

    def test_terraform_block(self):
        """
        Test the special 'terraform' configuration block.
        """
        block_after = {
            "block_identifiers": "terraform",
            "block_name": "terraform",
            "start_block": 1,
            "end_block": 5,
            "numAttrs": 1
        }
        block_before = {
            "block_identifiers": "terraform",
            "block_name": "terraform",
            "start_block": 1,
            "end_block": 5,
            "numAttrs": 1
        }
        
        blocks = self.create_impacted_blocks([block_after], [block_before], [3], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "terraform")

    def test_variable_and_output_blocks(self):
        """
        Test variable and output blocks.
        """
        var_block = {
            "block_identifiers": "variable.region",
            "block_name": "variable",
            "start_block": 10,
            "end_block": 13,
            "numAttrs": 1
        }
        output_block = {
            "block_identifiers": "output.instance_ip",
            "block_name": "output",
            "start_block": 20,
            "end_block": 23,
            "numAttrs": 1
        }
        
        # Change in output block (line 21)
        blocks = self.create_impacted_blocks(
            [var_block, output_block], 
            [var_block, output_block], 
            [21], 
            []
        )
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "output.instance_ip")

    def test_locals_block(self):
        """
        Test the locals block which defines local values.
        """
        block_after = {
            "block_identifiers": "locals",
            "block_name": "locals",
            "start_block": 15,
            "end_block": 20,
            "numAttrs": 3
        }
        block_before = {
            "block_identifiers": "locals",
            "block_name": "locals",
            "start_block": 15,
            "end_block": 19,
            "numAttrs": 2
        }
        
        # Line 18 modified (adding a new local value)
        blocks = self.create_impacted_blocks([block_after], [block_before], [18], [])
        impacted = blocks.identify_impacted_blocks_in_a_file("main.tf")
        
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["block_identifiers"], "locals")
        
        # Verify pairing works for locals
        pair = blocks.get_block(impacted[0], [block_before])
        self.assertIsNotNone(pair)
        self.assertEqual(pair["numAttrs"], 2, "Should match to before block with 2 attrs")

if __name__ == '__main__':
    unittest.main()
