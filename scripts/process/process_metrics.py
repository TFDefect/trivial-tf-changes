import numpy as np
from scripts.utility.commit_filters import get_subs_dire_name


class ProcessMetrics:

    def __init__(self, contribution, previous_contributions):
        # the current touched block before
        # include in the previous contribution
        self.contribution = contribution
        # the author of the change
        self.author = self.contribution["author"]
        # the touched file that contains the affected block
        self.file = self.contribution["file"]
        # the identifier of the current block
        self.identifier = self.contribution["block_identifiers"]
        # Current commit
        self.actualCommit = self.contribution["commit"]
        # the blocks touched before the current block
        self.previous_contributions = previous_contributions
        # the blocks touched by the same author, for the author experience
        self.blocks_changed_before_by_current_author = list(
            prev_contribution for prev_contribution in self.previous_contributions
            if prev_contribution["author"] == self.author
        )
        # the same blocks as the current changed block by the same author
        self.blocks_changed_before_by_author_as_current_changed_block = list(
            prev_contribution for prev_contribution in self.blocks_changed_before_by_current_author
            if prev_contribution["block_identifiers"] == self.identifier and
            prev_contribution["file"] == self.file
        )
        # the same blocks as the current changed block
        self.blocks_changed_before_as_current_changed_block_by_different_authors = list(
            prev_contribution for prev_contribution in self.previous_contributions
            if prev_contribution["block_identifiers"] == self.identifier and
            prev_contribution["file"] == self.file
        )

    def num_defects_in_block_before(self):
        defects = list(prev_contribution for prev_contribution in
                       self.blocks_changed_before_as_current_changed_block_by_different_authors
                       if prev_contribution["fault_prone"] == 1)
        return len(defects)

    def kexp(self):
        # The experience of the developer
        # with the kind of resource or data
        # resource "aws_instance_db" "a"
        # resource "aws_instance_db" "b"
        k_exp = 0
        if self.contribution["isResource"] == 1 or self.contribution["isData"] == 1:
            near_blocks = list(near_block for near_block
                               in self.blocks_changed_before_by_current_author
                               if near_block["block"] == self.contribution["block"] and
                               near_block["block_id"] == self.contribution["block_id"]
                               )
            k_exp = len(near_blocks)
        return k_exp

    def num_same_blocks_with_different_names_changed_before(self):
        number_instances_introduced_before = 0
        if self.contribution["isResource"] == 1 or self.contribution["isData"] == 1:
            near_duplicated = list(prev_contribution for prev_contribution
                                   in self.previous_contributions
                                   if prev_contribution["block"] == self.contribution["block"] and
                                   prev_contribution["block_id"] == self.contribution["block_id"])
            number_instances_introduced_before = len(near_duplicated)
        return number_instances_introduced_before

    def num_devs(self):
        """
        Number of developers that changed the block before
        :return:
        """
        unique_authors = set(prev_contribution["author"] for prev_contribution
                             in self.blocks_changed_before_as_current_changed_block_by_different_authors)
        ndev_count = len(unique_authors)
        return ndev_count

    def num_commits(self):
        """
        Number of commits that changed the block before
        :return:
        """
        commits_before = set(prev_contribution["commit"] for prev_contribution
                             in self.blocks_changed_before_as_current_changed_block_by_different_authors)
        commits_before_count = len(commits_before)
        return commits_before_count

    def num_unique_change(self):
        """
        How many unique changes that impacted the Current Block
        :return:
        """
        # Dictionary to store blocks grouped by their commits
        commits_dict = {}

        for changed_block_before in self.previous_contributions:
            commit = changed_block_before["commit"]

            # If this commit is not yet in the dictionary, initialize it with an empty list
            if commit not in commits_dict:
                commits_dict[commit] = []

            # Append the current block to this commit's list
            commits_dict[commit].append(changed_block_before)

        # Among the unique_changes, identify the number of changes that impacted the current block before
        impacted_current_block = sum(1 for blocks in commits_dict.values() if len(blocks) == 1 and
                                     blocks[0]["block_identifiers"] == self.identifier and
                                     blocks[0]["file"] == self.file)

        return impacted_current_block

    def code_ownership(self):
        """
        src ===> https://www.sciencedirect.com/science/article/pii/S0164121219302675?via%3Dihub
        Code ownership:
            given a Block b:
                - we compute the ratio of number of commits that a contributor c has made on m
                - with respect to the total number of commits made by c.
            Once computed the metric for all developers who contributed to m, we assign to the method the maximum ownership computed.
        :return:
        """
        current_author_experience = self.contribution["exp"]
        if current_author_experience != 0:
            return len(self.blocks_changed_before_by_author_as_current_changed_block) / current_author_experience

        return 0

    """
        Experience Features
    """

    def get_author_rexp(self):
        """
        The total experience of the developer in terms of commits,
        weighted by their age (more recent commit have a higher weight).
        Commits made by a developer with high relevant experience are less risky
        :return:
        """
        rexp = 0
        if self.blocks_changed_before_by_current_author:
            for lastBlock in self.blocks_changed_before_by_current_author:
                age = (self.contribution["date"] - lastBlock["date"]).days
                age = max(age, 0)
                rexp += 1 / (age + 1)
            return rexp
        return 0

    def get_author_bexp(self):
        """
        The total experience of the developer in terms of commits that modify
        the same type of block as the current changed block
        :return:
        """
        bexp = 0
        if self.blocks_changed_before_by_current_author:
            for lastBlock in self.blocks_changed_before_by_current_author:
                if (lastBlock["block"] == self.contribution["block"]) and \
                        (self.contribution["commit"] != lastBlock["commit"]):
                    # This case can be changed, if we assume that:
                    # FROM Kla: https://ieeexplore.ieee.org/document/9689967
                    # Given a changed file in a pull request, 80.6% of the respondents currently inspect source
                    # code in a top-down order. Once defective lines are identified, 72.2% of the respondents inspect
                    # the defective lines and their related method calls, while 52.8% of the respondents inspect
                    # the defective lines and their surrounding lines. Also, 50% of the respondents spent
                    # at least 10 minutes to more than one hour to review a single file, indicating that current
                    # code review activities are still time-consuming. Importantly, 64% of the respondents perceived
                    # that code inspection activity is very challenging to extremely challenging.
                    bexp += 1
            return bexp
        return 0

    def get_author_sexp(self):
        # Developer experience on a sub-system
        sexp = 0
        # Get the current subsystem
        current_changed_sub, _, _ = get_subs_dire_name(self.contribution["file"])
        subs = []
        if self.blocks_changed_before_by_current_author:
            for lastBlock in self.blocks_changed_before_by_current_author:
                sub, _, _ = get_subs_dire_name(lastBlock["file"])
                subs.append(sub)
                # If the current subsystem already exists and does not have the same commit
                # ==> "same date of pushing"
                if (current_changed_sub in subs) and (self.contribution["commit"] != lastBlock["commit"]):
                    sexp += 1
            return sexp
        return 0

    """
        History Features
    """

    def age(self):
        # Convert the commit dates to datetime objects
        current_dt = self.contribution["date"]
        ages = []
        if self.blocks_changed_before_as_current_changed_block_by_different_authors:

            for lastBlock in self.blocks_changed_before_as_current_changed_block_by_different_authors:
                recent_dt = lastBlock["date"]
                time_diff = current_dt - recent_dt
                age = time_diff.days
                age = max(age, 0)
                ages.append(age)
            return np.mean(ages)
        return 0.0

    def time_interval(self):
        blocks_before = self.blocks_changed_before_as_current_changed_block_by_different_authors
        # We take only the recent changed block before
        recent_block = blocks_before[-1] if blocks_before else None
        if recent_block:
            # Convert the commit dates to datetime objects
            current_dt = self.contribution["date"]
            # print(current_dt)
            recent_dt = recent_block["date"]
            # print(recent_dt)
            time_diff = current_dt - recent_dt
            return time_diff.days
        return 0

    """
        Export all the features
    """

    def resume_process_metrics(self):

        return {
            # Number of developers that changed the block before
            "ndevs": self.num_devs(),
            # Number of commits that changed the current block before
            "ncommits": self.num_commits(),
            # Number of change on 'b' by 'c', on the experience of 'c'
            "code_ownership": self.code_ownership(),
            # Experience by number of commits made by the author
            "exp": self.contribution["exp"],
            # Recent Experience
            "rexp": self.get_author_rexp(),
            # Experience with sub-system
            "sexp": self.get_author_sexp(),
            # Experience with blocks
            "bexp": self.get_author_bexp(),
            # Average Time Interval between the recent and the change before
            "age": self.age(),
            # Time Interval Between Two Changes
            "time_interval": self.time_interval(),
            # Number of defects before
            "num_defects_before": self.num_defects_in_block_before(),
            # Number of near-duplicated instances
            "num_same_instances_changed_before": self.num_same_blocks_with_different_names_changed_before(),
            # Experience of the author with the actual kind of resources
            "kexp": self.kexp(),
            # Count the number of unique commits that changed before the current block
            "num_unique_change": self.num_unique_change()
        }

    @staticmethod
    def get_headers():
        return [
            "ndevs", "ncommits", "code_ownership", "exp", "rexp", "sexp", "bexp", 
            "age", "time_interval", "num_defects_before", 
            "num_same_instances_changed_before", "kexp", "num_unique_change"
        ]
