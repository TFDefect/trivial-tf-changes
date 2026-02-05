
import unittest
import os
import sys
import csv

# Add project root to sys.path
sys.path.append(os.getcwd())

from scripts.collect_metrics import collect_metrics

class TestJITIntegration(unittest.TestCase):
    def test_jit_specific_commit(self):
        # The commit that removed 'ssh_pub_key' from 'module "kubernetes"'
        # We expect exactly 1 impacted block.
        # Testing with an older commit to ensure it DOES NOT traverse forward.
        # Commit a80c034... (add all TF blocks)
        target_commit = "484ac9e74d554e14da5d18b1e60003b94ccb577f"

        repo_path = os.getcwd()
        output_file = "metrics.csv"
        
        # Ensure fresh start
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print(f"Testing JIT metrics collection for commit: {target_commit}")
        
        # Run function directly (simulating CLI --commit)
        collect_metrics(repo_path, target_commit=target_commit)
        
        # Verify Output
        self.assertTrue(os.path.exists(output_file), "metrics.csv should be created")
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            print(f"Rows generated: {len(rows)}")
            for row in rows:
                print(f" - Impacted File: {row.get('file')}")
                print(f" - Block Name: {row.get('block_name')}")
                print(f" - Block Type: {row.get('block')}")
            
            # Assertions
            # Assertions
            self.assertEqual(len(rows), 2, "Should identify 2 impacted blocks for this commit (terraform, provider)") 
            # Note: The older commit had 2 blocks: terraform and provider google.
            # We verify we got rows ONLY for this commit.
            for row in rows:
                self.assertEqual(row['commit'], target_commit, "Row commit hash should match target exactly")


if __name__ == '__main__':
    unittest.main()
