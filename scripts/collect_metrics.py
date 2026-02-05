import os
import sys
import tempfile
import argparse
import csv
from pydriller import Repository

# Add project root to sys.path
sys.path.append(os.getcwd())

from scripts.impacted_block_detection import ImpactedBlocks
from scripts.process.process_metrics import ProcessMetrics
from scripts.edits.similarity_change import SimilarityChange
from scripts.process.lines_change.ImpactedLines import ImpactedLines
from scripts.process.attr_terraform_change.attr_change import AttrChange
from scripts.utility.commit_filters import is_undesired_commit, beSafeFromSpecialCommit

# Global context for history (can be passed around or kept global for full run)
# previous_contributions = []
# author_commits_count = {}

def get_author_experience(author_commits_count, author_name):
    return author_commits_count.get(author_name, 0)

def update_author_experience(author_commits_count, author_name):
    author_commits_count[author_name] = author_commits_count.get(author_name, 0) + 1

def process_commit(commit, previous_contributions, author_commits_count):
    """
    Process a single commit to calculate defect metrics for all modified Terraform files.
    
    Args:
        commit: pydriller.Commit object.
        previous_contributions: List of prior contribution dicts (for context-aware metrics).
        author_commits_count: Dict of author experience stats.
        
    Returns:
        List[dict]: A list of contribution dictionaries (one per impacted block) calculated for this commit.
    """
    contributions = []
    
    contributions = []
    
    # Filters
    try:
        if is_undesired_commit(commit):
            return []
        if not beSafeFromSpecialCommit(commit.msg):
            return []
    except Exception as e:
        # In case filters fail
        return []

    author = commit.author.name
    exp = get_author_experience(author_commits_count, author)
    update_author_experience(author_commits_count, author)

    cleanCommitMessage = commit.msg.strip()

    for mod in commit.modified_files:
        if not mod.filename.endswith('.tf'):
            continue

        # Create temp files for BlockIdentificator (used by SimilarityChange)
        pathAfterChange = None
        pathBeforeChange = None

        try:
            # Write temp file for After content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False, encoding='utf-8') as f_after:
                f_after.write(mod.source_code if mod.source_code else "")
                pathAfterChange = f_after.name

            # Write temp file for Before content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False, encoding='utf-8') as f_before:
                f_before.write(mod.source_code_before if mod.source_code_before else "")
                pathBeforeChange = f_before.name

            impactedBlockInstance = ImpactedBlocks(mod, file_ext_to_parse=['tf'])
            impactedBlocks = impactedBlockInstance.identify_impacted_blocks_in_a_file(mod.filename)

            if impactedBlocks:
                print(f"Impacted blocks found for {mod.filename}: {len(impactedBlocks)} blocks")
                for block in impactedBlocks:
                    # 0. Contribution
                    contribution = {
                        "file": mod.filename,
                        "author": author,
                        "commit": commit.hash,
                        "exp": exp,
                        "date": commit.committer_date,
                        "msg": cleanCommitMessage
                    }

                    # Add block details (contains the huge list of features)
                    contribution.update(block)

                    # Get block before change
                    blockBeforeChange = impactedBlockInstance.get_block(block,
                                                                        impactedBlockInstance.blocks_before_change)

                    # 4. Process Metrics
                    process = ProcessMetrics(contribution, previous_contributions)
                    contribution.update(process.resume_process_metrics())

                    # 3. Similarity Change
                    similarityChange = SimilarityChange(block, pathAfterChange, blockBeforeChange, pathBeforeChange)
                    contribution.update(similarityChange.resume_similarity_change())

                    # 1. Impacted Lines
                    impactedLines = ImpactedLines(mod, block, blockBeforeChange)
                    contribution.update(impactedLines.resume_changed_lines())

                    # 2. Attr Change
                    attrChange = AttrChange(block, impactedLines.additions, impactedLines.deletions)
                    contribution.update(attrChange.resume_changed_attr())
                    
                    contributions.append(contribution)

        except Exception as e:
            # print(f"Error processing {mod.filename}: {e}", file=sys.stderr)
            pass
        finally:
            if pathAfterChange and os.path.exists(pathAfterChange):
                os.remove(pathAfterChange)
            if pathBeforeChange and os.path.exists(pathBeforeChange):
                os.remove(pathBeforeChange)
    
    return contributions

def collect_metrics(repo_path, target_commit=None):
    print(f"Starting metrics collection on: {repo_path}")
    if target_commit:
        print(f"Targeting single commit: {target_commit}")

    output_file = "metrics.csv"
    
    # Context
    previous_contributions = []
    author_commits_count = {}

    # We will determine headers dynamically from the first valid contribution
    headers = None
    file_exists = os.path.isfile(output_file)

    # Logic:
    # If target_commit is set, we assume JIT mode. 
    # Logic for JIT: Only process the specific commit.
    # Note: For strict JIT without hydrating previous_contributions from history, metrics depending on history 
    # (like ndevs, exp, num_defects_before) starts from 0/empty. 
    # If the user wants full context for JIT, they would need to load history or traverse up to that point.
    # Assuming standard behavior -> process just this commit with empty context OR traverse until found.
    # To support "just-in-time extraction (commit being committed in github)", usually implies fast execution.
    # We will implement "Process ONLY this commit" for now.
    
    # Remove existing file if it exists to start fresh ONLY if we are doing a full run
    if not target_commit and os.path.exists(output_file):
        os.remove(output_file)
        file_exists = False
    
    # Repo traversal
    if target_commit:
        # JIT Mode: Only process the specific commit
        # We need to find the commit object. pydriller can iterate slightly to find it or we assume it's HEAD if checked out
        # Using single commit traversal
        repo_mining = Repository(repo_path, single=target_commit)
    else:
        # Full Mode
        repo_mining = Repository(repo_path, order='reverse')

    count = 0
    for commit in repo_mining.traverse_commits():
        
        # In JIT mode with single=hash, loop runs once.
        
        new_contributions = process_commit(commit, previous_contributions, author_commits_count)
        
        if new_contributions:
            # Determine headers if needed
            if headers is None:
                # If file exists (e.g. appending in JIT), read headers from it?
                # Or just use the new keys. 
                # If we are appending to an existing file, we should arguably verify headers match or just proceed.
                # For safety, let's derive from data.
                if file_exists:
                     with open(output_file, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        try:
                            headers = next(reader)
                        except StopIteration:
                            pass # File empty
                
                if headers is None or len(headers) == 0:
                    headers = list(new_contributions[0].keys())
                    print(f"Dynamic Headers determined ({len(headers)} columns)")
            
            # Write results
            with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
                
                if not file_exists:
                    writer.writeheader()
                    file_exists = True # Header written
                
                for contribution in new_contributions:
                    writer.writerow(contribution)
            
            # Update history
            previous_contributions.extend(new_contributions)
        
        count += 1
        # Optional: break for testing if too long
        # if not target_commit and count > 10: break

    print(f"Metrics collection complete. Output saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect Terraform metrics.")
    parser.add_argument("repo_path", type=str, nargs="?", default=os.getcwd(), help="Path to the repository")
    parser.add_argument("--commit", type=str, help="Specific commit hash to process (JIT mode)")
    
    args = parser.parse_args()
    
    collect_metrics(args.repo_path, args.commit)
