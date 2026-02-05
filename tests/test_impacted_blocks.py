
import os
import sys

# Ensure project root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydriller import Repository
from scripts.impacted_block_detection import ImpactedBlocks

def test_impacted_blocks():
    # Detect the current repo path
    repo_path = os.getcwd()
    print(f"Scanning repository at: {repo_path}")
    
    # Traverse the latest commits (last 1)
    for commit in Repository(repo_path, order='reverse').traverse_commits():
        print(f"Analyzing Commit: {commit.hash} - {commit.msg}")
        
        for mod in commit.modified_files:
            if not mod.filename.endswith('.tf'):
                continue
                
            print(f"  Checking file: {mod.filename}")
            
            try:
                impacted = ImpactedBlocks(mod, file_ext_to_parse=['tf'])
                blocks = impacted.identify_impacted_blocks_in_a_file(mod.filename)
                
                if blocks:
                    print(f"  >> Modified Blocks Detected in {mod.filename}:")
                    for b in blocks:
                        print(f"     - Block: {b.get('block_identifiers')}")
                        print(f"       Range: {b.get('start_block')}-{b.get('end_block')}")
                        # Print other keys to show metrics if available
                        print(f"       Details: {b}")
                else:
                    print(f"  >> No impacted blocks detected in {mod.filename}")
                    
            except Exception as e:
                print(f"  !! Error analyzing file: {e}")
                import traceback
                traceback.print_exc()

        # Just check the latest commit for this test
        break

if __name__ == "__main__":
    test_impacted_blocks()
