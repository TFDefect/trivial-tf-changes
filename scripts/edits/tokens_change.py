from pydriller import ModifiedFile

from scripts.process.lines_change.ImpactedLines import ImpactedLines


class TokensChange(ImpactedLines):

    def __init__(self, mod: ModifiedFile, block, blockBefore):
        super().__init__(mod, block, blockBefore)

    def resume_token_change(self):

       return {"sum_removed_line_token":  0 if self.deletions is None else self.deletions.sum_removed_line_token(),
                        "avg_removed_line_token":  0 if self.deletions is None else self.deletions.avg_removed_line_token(),
                        "max_removed_line_token":  0 if self.deletions is None else self.deletions.max_removed_line_token(),
                        "sum_removed_line_length": 0 if self.deletions is None else self.deletions.sum_removed_line_length(),
                        "avg_removed_line_length": 0 if self.deletions is None else self.deletions.avg_removed_line_length(),
                        "max_removed_line_length": 0 if self.deletions is None else self.deletions.max_removed_line_length(),
                        "text_entropy_for_removed_lines": 0 if self.deletions is None else self.deletions.text_entropy_for_removed_lines(),
                        "sum_added_line_token": 0 if self.additions is None else self.additions.sum_added_line_token(),
                        "avg_added_line_token": 0 if self.additions is None else self.additions.avg_added_line_token(),
                        "max_added_line_token": 0 if self.additions is None else self.additions.max_added_line_token(),
                        "sum_added_line_length": 0 if self.additions is None else self.additions.sum_added_line_length(),
                        "avg_added_line_length": 0 if self.additions is None else self.additions.avg_added_line_length(),
                        "max_added_line_length": 0 if self.additions is None else self.additions.max_added_line_length(),
                        "text_entropy_for_added_lines": 0 if self.additions is None else self.additions.text_entropy_for_added_lines()
        }

