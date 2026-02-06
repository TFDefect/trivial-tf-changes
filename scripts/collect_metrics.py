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
from scripts.process.delta_metrics import DeltaMetrics
from scripts.utility.commit_filters import is_undesired_commit, beSafeFromSpecialCommit

# Global context for history (can be passed around or kept global for full run)
# previous_contributions = []
# author_commits_count = {}

def get_author_experience(author_commits_count, author_name):
    return author_commits_count.get(author_name, 0)

def update_author_experience(author_commits_count, author_name):
    author_commits_count[author_name] = author_commits_count.get(author_name, 0) + 1

def load_history_from_csv(csv_path):
    """
    Load previous contributions and author experience from existing metrics.csv.
    
    Args:
        csv_path: Path to the historical metrics CSV file
        
    Returns:
        tuple: (previous_contributions list, author_commits_count dict)
    """
    previous_contributions = []
    author_commits_count = {}
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Add to previous contributions
                # Convert date string back to datetime if needed
                if 'date' in row and row['date']:
                    try:
                        from datetime import datetime
                        row['date'] = datetime.fromisoformat(row['date'])
                    except:
                        pass  # Keep as string if conversion fails
                
                previous_contributions.append(row)
                
                # Track author experience (count unique commits per author)
                author = row.get('author')
                commit = row.get('commit')
                if author and commit:
                    if author not in author_commits_count:
                        author_commits_count[author] = set()
                    author_commits_count[author].add(commit)
        
        # Convert sets to counts
        author_commits_count = {author: len(commits) for author, commits in author_commits_count.items()}
        
    except Exception as e:
        print(f"Warning: Could not load history from {csv_path}: {e}")
        return [], {}
    
    return previous_contributions, author_commits_count


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

                    # 5. Delta Metrics
                    delta = DeltaMetrics(block, blockBeforeChange)
                    contribution.update(delta.compute_delta_metrics())
                    
                    contributions.append(contribution)

        except Exception as e:
            print(f"Error processing {mod.filename}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            pass
        finally:
            if pathAfterChange and os.path.exists(pathAfterChange):
                os.remove(pathAfterChange)
            if pathBeforeChange and os.path.exists(pathBeforeChange):
                os.remove(pathBeforeChange)
    
    return contributions

    return contributions

def collect_metrics_jit(repo_path, target_commit, history_file=None):
    """
    Collect metrics for a specific commit (Just-In-Time).
    
    Args:
        repo_path: Path to the repository
        target_commit: Commit hash to analyze
        history_file: Optional path to previous metrics.csv for historical context
    """
    print(f"Starting JIT metrics collection on: {repo_path} for commit {target_commit}")
    
    # File naming convention:
    # - metrics.csv: Current run metrics only
    # - metrics_history.csv: All accumulated historical metrics
    current_metrics_file = "metrics.csv"
    history_metrics_file = "metrics_history.csv"
    
    # JIT context - can be hydrated from history file
    previous_contributions = []
    author_commits_count = {}
    
    # Load historical context if provided
    if history_file and os.path.exists(history_file):
        print(f"Loading historical context from: {history_file}")
        previous_contributions, author_commits_count = load_history_from_csv(history_file)
        print(f"Loaded {len(previous_contributions)} previous contributions")
        print(f"Loaded {len(author_commits_count)} authors")

    # Process specific commit
    repo_mining = Repository(repo_path, single=target_commit)
    
    headers = None
    new_contributions_list = []
    
    for commit in repo_mining.traverse_commits():
        new_contributions = process_commit(commit, previous_contributions, author_commits_count)
        
        if new_contributions:
            if headers is None:
                headers = list(new_contributions[0].keys())
                print(f"Dynamic Headers determined ({len(headers)} columns)")
            new_contributions_list.extend(new_contributions)
    
    # Write current metrics to metrics.csv
    if new_contributions_list:
        with open(current_metrics_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            for contribution in new_contributions_list:
                writer.writerow(contribution)
        print(f"Wrote {len(new_contributions_list)} rows to {current_metrics_file}")
        
        # Merge current with history to create accumulated metrics_history.csv
        if history_file and os.path.exists(history_file):
            print(f"Merging current metrics with history...")
            merge_metrics_files(history_file, current_metrics_file, history_metrics_file)
        else:
            # No history, copy current to history
            import shutil
            shutil.copy(current_metrics_file, history_metrics_file)
        
        print(f"JIT Metrics collection complete.")
        print(f"  Current metrics: {current_metrics_file}")
        print(f"  Historical metrics: {history_metrics_file}")
    else:
        print("No metrics collected for this commit")

def merge_metrics_files(history_file, new_file, output_file):
    """
    Merge history and new metrics into a single output file.
    
    Args:
        history_file: Path to historical metrics
        new_file: Path to newly collected metrics
        output_file: Path to merged output
    """
    import pandas as pd
    
    # Read both files
    df_history = pd.read_csv(history_file)
    df_new = pd.read_csv(new_file)
    
    # Combine
    df_combined = pd.concat([df_history, df_new], ignore_index=True)
    
    # Remove duplicates (same commit + file + block_identifiers)
    if 'commit' in df_combined.columns and 'file' in df_combined.columns:
        df_combined = df_combined.drop_duplicates(
            subset=['commit', 'file', 'block_identifiers'],
            keep='last'
        )
    
    # Write combined file
    df_combined.to_csv(output_file, index=False)
    print(f"Merged: {len(df_history)} history + {len(df_new)} new = {len(df_combined)} total rows")


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

def collect_metrics(repo_path, target_commit=None, history_file=None):
    if target_commit:
        collect_metrics_jit(repo_path, target_commit, history_file)
    else:
        collect_metrics_full(repo_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect Terraform metrics.")
    parser.add_argument("repo_path", type=str, nargs="?", default=os.getcwd(), help="Path to the repository")
    parser.add_argument("--commit", type=str, help="Specific commit hash to process (JIT mode)")
    parser.add_argument("--history", type=str, help="Path to previous metrics.csv for historical context (JIT mode only)")
    
    args = parser.parse_args()
    collect_metrics(args.repo_path, args.commit, args.history)

def main():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description="Collect Terraform metrics.")
    parser.add_argument("repo_path", type=str, nargs="?", default=os.getcwd(), help="Path to the repository")
    parser.add_argument("--commit", type=str, help="Specific commit hash to process (JIT mode)")
    parser.add_argument("--history", type=str, help="Path to previous metrics.csv for historical context (JIT mode only)")
    
    args = parser.parse_args()
    collect_metrics(args.repo_path, args.commit, args.history)

if __name__ == "__main__":
    main()
