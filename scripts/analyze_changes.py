
import os
import sys

# Ensure project root is on sys.path
sys.path.append(os.getcwd())

from pydriller import Repository
from scripts.impacted_block_detection import ImpactedBlocks

def analyze_changes():
    # In GitHub Actions, the repo is checked out to GITHUB_WORKSPACE (current wdir)
    repo_path = os.getcwd()
    print(f"Starting Terraform Change Analysis in: {repo_path}")
    
    # We want to analyze the latest commit (HEAD)
    # In a PR, this might be a merge commit or the head of the branch.
    # We'll use traverse_commits to get the last one.
    
    # Note: ensure fetch-depth: 0 is used in checkout to get history
    
    count = 0
    # Traverse only the single latest commit
    for commit in Repository(repo_path, order='reverse').traverse_commits():
        print(f"::group::Analyzing Commit {commit.hash}")
        print(f"Message: {commit.msg}")
        print(f"Author: {commit.author.name}")
        
        modified_blocks_found = False
        
        for mod in commit.modified_files:
            if not mod.filename.endswith('.tf'):
                continue
                
            print(f"Analyzing file: {mod.filename}")
            
            try:
                impacted = ImpactedBlocks(mod, file_ext_to_parse=['tf'])
                blocks = impacted.identify_impacted_blocks_in_a_file(mod.filename)
                
                if blocks:
                    modified_blocks_found = True
                    print(f"  Result: ⚠️ Modified Blocks Detected in {mod.filename}")
                    for b in blocks:
                        # Use GitHub Actions annotation format if desired, or just print
                        start = b.get('start_block')
                        end = b.get('end_block')
                        ident = b.get('block_identifiers', 'unknown')
                        print(f"    - Block: {ident} (Lines {start}-{end})")
                else:
                    print(f"  Result: ✅ No impacted blocks detected in {mod.filename}")
                    
            except Exception as e:
                print(f"  Error analyzing {mod.filename}: {e}")
                # Don't fail the build for analysis errors unless requested, just log it.

        print("::endgroup::")
        
        if modified_blocks_found:
             print("::notice::Terraform blocks were modified in this commit.")
        
        count += 1
        if count >= 1: # Only analyze the last commit
            break

if __name__ == "__main__":
    analyze_changes()
