
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from scripts.impacted_block_detection import ImpactedBlocks

class TestBlockIsolation(unittest.TestCase):
    def setUp(self):
        # Mock the ModifiedFile object
        self.mock_mod = MagicMock()
        self.mock_mod.filename = "test.tf"
        self.mock_mod.source_code = """
resource "aws_instance" "foo" {
  ami = "ami-123"
  instance_type = "t2.micro"
}

resource "aws_s3_bucket" "bar" {
  bucket = "my-bucket"
  acl    = "private"
}
"""
        self.mock_mod.source_code_before = """
resource "aws_instance" "foo" {
  ami = "ami-123"
  instance_type = "t2.micro"
}

resource "aws_s3_bucket" "bar" {
  bucket = "my-bucket"
  acl    = "public-read"
}
"""
        # Mock diff: changed "acl" line in the second block
        # Blocks:
        # foo: lines 2-5
        # bar: lines 7-10
        # Change is at line 9 (acl)
        
        # We need to mock the CodeMetricsExtractor or the _get_blocks method because it calls external JAR
        # To avoid running Java during unit test, we can mock _get_blocks return value
        
    def test_impacted_blocks_filtering(self):
        # Initialize
        detector = ImpactedBlocks(self.mock_mod, file_ext_to_parse=['tf'])
        
        # Mock _get_blocks return values (parsed blocks)
        # Note: start_block/end_block typically exclude the header? or include?
        # Based on previous logs: "start_block": 20, "end_block": 42
        # Let's assume inclusive or bounding lines.
        
        blocks_after = [
            {
                "block_name": "aws_instance",
                "block_identifiers": "resource aws_instance foo",
                "start_block": 2,
                "end_block": 5,
                "numAttrs": 2
            },
            {
                "block_name": "aws_s3_bucket",
                "block_identifiers": "resource aws_s3_bucket bar",
                "start_block": 7,
                "end_block": 10,
                "numAttrs": 2
            }
        ]
        
        detector.blocks_after_change = blocks_after
        detector.blocks_before_change = blocks_after # Structure same
        detector.status_after_change = 200
        detector.status_before_change = 200
        
        # Mock added lines: line 9 changed
        detector.added_lines = [9] 
        # mock deleted lines
        detector.removed_lines = [9]
        
        # Act
        impacted = detector.identify_impacted_blocks_in_a_file("test.tf")
        
        # Assert
        self.assertIsNotNone(impacted)
        self.assertEqual(len(impacted), 1, f"Expected 1 impacted block, found {len(impacted)}")
        self.assertEqual(impacted[0]['block_identifiers'], "resource aws_s3_bucket bar")
        print("\nTest Passed: Only 'aws_s3_bucket bar' was identified as impacted.")

if __name__ == '__main__':
    unittest.main()
