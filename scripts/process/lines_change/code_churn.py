from scripts.process.lines_change.additions import Additions
from scripts.process.lines_change.deletions import Deletions


class CodeChurn:
    """
    This class is responsible to implement the Code Churn metric for a Block Hcl.
    Depending on the parametrization of this class, a code churn is the sum of either
    (added lines_change + removed lines_change)
    across the analyzed commits. It allows counting for the:
    * total number of codes churns - count();
    * maximum codes churn for all commits - max();
    * average codes churn per commit.
    """

    def __init__(self, mod, blockBeforeChange, blockAfterChange):
        self.mod = mod
        self.blockBeforeChange = blockBeforeChange
        self.blockAfterChange = blockAfterChange

    def count_code_churn_block(self):
        additions = Additions(self.mod, self.blockAfterChange["start_block"], self.blockAfterChange["end_block"])
        deletionsCpt = 0

        if self.blockBeforeChange is not None:
            deletions = Deletions(self.mod, self.blockBeforeChange["start_block"], self.blockBeforeChange["end_block"])
            deletionsCpt = deletions.count_deleted_lines_in_a_block()

        # if self.add_deleted_lines_to_churn:
        # if add_deleted_lines_to_churn:
        #     return additions.count_added_lines_in_a_block() + deletionsCpt
        return additions.count_added_lines_in_a_block() + deletionsCpt
