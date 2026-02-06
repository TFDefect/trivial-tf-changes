
class DeltaMetrics:
    def __init__(self, block_after, block_before):
        """
        Calculates the difference between metrics before and after modification.
        
        Args:
            block_after (dict): Metrics of the block after change.
            block_before (dict): Metrics of the block before change.
        """
        self.block_after = block_after
        self.block_before = block_before

    def compute_delta_metrics(self) -> dict:
        """
        Returns:
            dict: Delta metrics (e.g., {'val_delta': 2})
        """
        delta_results = {}

        if not self.block_after:
            return delta_results

        # If block_before is missing (new block), we can assume previous values were 0 for numeric fields
        # OR we can decide to only compute deltas if both exist.
        # User snippet implied: "if before_block is None: logger.warning(...); continue"
        # However, for a "new block", delta = value - 0 = value seems logical for counts.
        # But let's follow the user's implication of "comparison".
        # If I treat None as empty dict, I get value - 0. Let's do that for robustness.
        
        before_data = self.block_before if self.block_before else {}
        
        for key, after_value in self.block_after.items():
            # filters
            if key in ["block_identifiers", "block_name", "start_block", "end_block"]:
                continue
                
            if isinstance(after_value, (int, float)):
                before_value = before_data.get(key, 0)
                if isinstance(before_value, (int, float)):
                    # We append _delta suffix
                    delta_results[f"{key}_delta"] = after_value - before_value

        return delta_results
