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
                for b in impactedBlocks:
                    print(f" - Block: {b.get('block_name')} ({b.get('start_block')}-{b.get('end_block')})")
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

    return contributions

def collect_metrics_jit(repo_path, target_commit):
    """
    Collect metrics for a specific commit (Just-In-Time).
    """
    print(f"Starting JIT metrics collection on: {repo_path} for commit {target_commit}")
    output_file = "metrics.csv"
    
    # JIT context (empty for now, can be hydrated if needed)
    previous_contributions = []
    author_commits_count = {}

    # Check for existing headers
    headers = None
    file_exists = os.path.isfile(output_file)
    if file_exists:
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                pass

    # Process specific commit
    repo_mining = Repository(repo_path, single=target_commit)
    
    for commit in repo_mining.traverse_commits():
        new_contributions = process_commit(commit, previous_contributions, author_commits_count)
        
        if new_contributions:
            if headers is None:
                headers = list(new_contributions[0].keys())
                print(f"Dynamic Headers determined ({len(headers)} columns)")
            
            with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
                if not file_exists:
                    writer.writeheader()
                    file_exists = True
                for contribution in new_contributions:
                    writer.writerow(contribution)
        
    print(f"JIT Metrics collection complete for commit {target_commit}.")

def collect_metrics_full(repo_path):
    """
    Collect metrics for the entire repository history.
    """
    print(f"Starting FULL metrics collection on: {repo_path}")
    output_file = "metrics.csv"
    
    # Remove existing file for full run
    if os.path.exists(output_file):
        os.remove(output_file)
    
    previous_contributions = []
    author_commits_count = {}
    headers = None
    file_exists = False

    repo_mining = Repository(repo_path, order='reverse')
    
    for commit in repo_mining.traverse_commits():
        new_contributions = process_commit(commit, previous_contributions, author_commits_count)
        
        if new_contributions:
            if headers is None:
                headers = list(new_contributions[0].keys())
                print(f"Dynamic Headers determined ({len(headers)} columns)")
            
            with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
                if not file_exists:
                    writer.writeheader()
                    file_exists = True
                for contribution in new_contributions:
                    writer.writerow(contribution)
            
            previous_contributions.extend(new_contributions)
            
    print(f"Full Metrics collection complete. Output saved to {output_file}")

def collect_metrics(repo_path, target_commit=None):
    if target_commit:
        collect_metrics_jit(repo_path, target_commit)
    else:
        collect_metrics_full(repo_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect Terraform metrics.")
    parser.add_argument("repo_path", type=str, nargs="?", default=os.getcwd(), help="Path to the repository")
    parser.add_argument("--commit", type=str, help="Specific commit hash to process (JIT mode)")
    
    args = parser.parse_args()
    collect_metrics(args.repo_path, args.commit)
