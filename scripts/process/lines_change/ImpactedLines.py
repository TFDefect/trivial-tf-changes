from pydriller import ModifiedFile
from scripts.process.lines_change.additions import Additions
from scripts.process.lines_change.code_churn import CodeChurn
from scripts.process.lines_change.deletions import Deletions


class ImpactedLines:

    def __init__(self, mod: ModifiedFile, block, blockBefore):
        self.mod = mod
        # current block
        self.block = block
        # the same block that changed before
        self.blockBefore = blockBefore
        # churn of change
        self.churn = CodeChurn(self.mod, self.blockBefore, self.block)
        self.additions = Additions(self.mod, self.block["start_block"], self.block["end_block"])
        self.deletions = None
        if blockBefore is not None:
            self.deletions = Deletions(self.mod, self.blockBefore["start_block"], self.blockBefore["end_block"])

    """
       Code Churn Features
    """
    def get_num_added_lines(self):
        numOfAdditions = self.additions.count_added_lines_in_a_block()
        return numOfAdditions

    # Number of deleted lines_change inside a block,
    def get_num_deleted_lines(self):
        if self.deletions is not None:
            return self.deletions.count_deleted_lines_in_a_block()
        return 0

    # Number of the churn lines_change
    def get_churn_size(self):
        churn_size = self.churn.count_code_churn_block()
        return churn_size

    """
        Diffusion Features
    """

    def get_num_added_lines_diffused(self):
        lab = self.get_num_added_lines()
        laf = len(self.additions.get_added_lines_in_a_file())
        if laf != 0:
            return lab / laf
        return 0.0

    def get_num_deleted_lines_diffused(self):
        ldb = self.get_num_deleted_lines()
        if self.deletions is not None:
            ldf = len(self.deletions.get_deleted_lines_in_a_file())
            if ldf != 0:
                return ldb / ldf
        return 0.0

    def resume_changed_lines(self):

        return {
            "additions": self.get_num_added_lines(),
            "deletions": self.get_num_deleted_lines(),
            "churn_size": self.get_churn_size(),
            "size_block_before_change": 0 if self.blockBefore is None else self.blockBefore["depthOfBlock"],

            "additions_normalized": 0 if self.blockBefore is None else self.get_num_added_lines() / self.blockBefore["depthOfBlock"],
            "deletions_lines_normalized": 0 if self.blockBefore is None else self.get_num_deleted_lines() / self.blockBefore["depthOfBlock"],
            "churn_size_normalized": 0 if self.blockBefore is None else self.get_churn_size() / self.blockBefore["depthOfBlock"],

            "additions_diffusion": self.get_num_added_lines_diffused(),
            "deletions_diffusion": self.get_num_deleted_lines_diffused()
        }

    @staticmethod
    def get_headers():
        return [
            "additions", "deletions", "churn_size", "size_block_before_change",
            "additions_normalized", "deletions_lines_normalized", "churn_size_normalized",
            "additions_diffusion", "deletions_diffusion"
        ]