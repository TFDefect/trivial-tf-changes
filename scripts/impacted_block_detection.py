import re
import os
import pydriller
from pydriller import ModificationType
# Fix import - CodeMetricsExtractor is in scripts.codes.code_metrics_measures
# but we need to ensure python path is correct or use relative imports if run as module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.codes.code_metrics_measures import CodeMetricsExtractor
from scripts.process.lines_change.additions import Additions
from scripts.process.lines_change.deletions import Deletions

class ImpactedBlocks:

    def __init__(self, mod, file_ext_to_parse=None):
        self.mod = mod
        self.file_ext_to_parse = file_ext_to_parse
        # Use the correct class and jar path
        jar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "libs", "terraform_metrics-1.0.jar")
        self.blockLocatorInstance = CodeMetricsExtractor(jar_path=jar_path)

        # status, data after the block changed
        # CodeMetricsExtractor.extract_metrics takes a dict {filename: [content]}? 
        # No, let's check extract_metrics signature. 
        # It takes modified_blocks: Dict[str, List[str]] where List[str] is list of BLOCKS?
        # Wait, the user's CodeMetricsExtractor seems to expect "modified blocks" as input to run the JAR?
        # The JAR usage says: --file <tf_path> -b --target <output_path>
        # So it analyzes a FILE.
        
        # We need to adapt to what CodeMetricsExtractor expects or use it differently.
        # The user's CodeMetricsExtractor.extract_metrics implementation writes content to temp file.
        
        # Let's try to pass the file content.
        # But wait, the original code used call_service_locator(before=True/False)
        # The NEW CodeMetricsExtractor doesn't have call_service_locator. 
        
        # I need to implement a compatibility layer or use the new one correctly.
        # The new one has `extract_metrics` and `_run_terrametrics`.
        
        # If I want to analyze the whole file content (before/after), I should probably use the JAR directly or method that does that.
        # _run_terrametrics runs on a file.
        
        # Let's implement a helper to extract metrics for a specific file content
        self.blocks_after_change = self._get_blocks(self.mod.source_code)
        self.blocks_before_change = self._get_blocks(self.mod.source_code_before)
        
        # Set status/head for compatibility if needed, but we mostly need the blocks list
        self.status_after_change = 200 if self.blocks_after_change else 404
        self.status_before_change = 200 if self.blocks_before_change else 404

        # Get added and removed lines_change
        self.additions = Additions(self.mod)
        self.added_lines = self.additions.get_added_lines_in_a_file()
        self.added_lines_content = self.additions.get_added_lines_content_in_a_file()
        self.deletions = Deletions(self.mod)
        self.removed_lines = self.deletions.get_deleted_lines_in_a_file()

    def _get_blocks(self, source_code):
        if not source_code:
            return []
        
        # We can use the CodeMetricsExtractor to parse this source code
        # But extract_metrics expects {filename: [blocks]}, and writes blocks to a file.
        # If we just want to run the JAR on the content:
        import tempfile
        import json
        
        if not source_code:
            return []
            
        with tempfile.NamedTemporaryFile(suffix=".tf", delete=False, mode="w", encoding='utf-8') as tf_file:
            tf_file.write(source_code)
            tf_path = tf_file.name
            
        json_path = tf_path + ".json"
        
        try:
            self.blockLocatorInstance._run_terrametrics(tf_path, json_path)
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    data = json.load(f)
                    # The JAR output format seems to be what we need.
                    # Based on old code: data["data"] is the blocks list
                    return data.get("data", [])
        except Exception as e:
            print(f"Error extracting blocks: {e}")
            return []
        finally:
            if os.path.exists(tf_path): os.remove(tf_path)
            if os.path.exists(json_path): os.remove(json_path)

    def is_dict_in_list(self, target_dict, list_of_dicts):
        for d in list_of_dicts:
            if d.get("block_identifiers") == target_dict.get("block_identifiers"):
                return True
        return False

    def get_block(self, block, list_of_dicts):
        minDistance = float('inf')
        closestBlock = None

        for d in list_of_dicts:
            if block.get("block_identifiers") == d.get("block_identifiers"):
                distance = abs(block.get("start_block", 0) - d.get("start_block", 0))
                if distance <= minDistance:
                    minDistance = distance
                    closestBlock = d
        return closestBlock

    def is_block_exist(self, block, list_of_dicts):
        closestBlock = self.get_block(block, list_of_dicts)
        if closestBlock is not None:
            return True
        return False

    def identify_impacted_blocks_in_a_file(self, file_path):

        if file_path is not None:

            impacted_blocks = []
            if self.status_before_change != 404 or self.status_after_change != 404:

                for obj in self.blocks_after_change:
                    for line in self.added_lines:
                        if not self.is_dict_in_list(obj, impacted_blocks):
                            if obj["start_block"] < line < obj["end_block"]:
                                impacted_blocks.append(obj)

                # --- Completeness
                if self.blocks_before_change is not None:
                    for obj in self.blocks_before_change:
                        cpt = 0
                        if not self.is_block_exist(obj, impacted_blocks):
                            for line in self.removed_lines:
                                if obj["start_block"] < line < obj["end_block"]:
                                    cpt += 1

                            if cpt == obj.get("numAttrs", 0): # Assuming numAttrs exists or 0
                                pass
                            elif obj.get("numAttrs", 0) > cpt >= 1:
                                target_block = self.get_block(obj, self.blocks_after_change)
                                if target_block is not None:
                                    impacted_blocks.append(target_block)

                return impacted_blocks
        return None
