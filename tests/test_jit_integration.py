
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
        # The commit that removed 'ssh_pub_key' from 'module "kubernetes"'
        # We expect exactly 1 impacted block.
        target_commit = "b7a5df34ec7e520db89e213d72599bf905262ae9"


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
            self.assertEqual(len(rows), 1, "Should identify 1 impacted block for this commit") 
            # Note: Commit b7a5df3 has 1 modified block (kubernetes module).
            # We verify we got rows ONLY for this commit.
            for row in rows:
                self.assertEqual(row['commit'], target_commit, "Row commit hash should match target exactly")
                
                # Check for Delta Metrics
                self.assertIn('numAttrs_delta', row, "Delta metric 'numAttrs_delta' should be present")
                print(f" - Delta Check: numAttrs_delta = {row.get('numAttrs_delta')}")



if __name__ == '__main__':
    unittest.main()
