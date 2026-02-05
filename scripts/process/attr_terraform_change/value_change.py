import re


class ValueAttrChange:

    def __init__(self, additions, deletions):
        self.additions = additions
        self.deletions = deletions

    def additions_contains_value_output_change(self):
        addedLinesInBlock = self.additions.get_added_lines_in_a_block()
        for numLine, contentLine in self.additions.added_lines_content:
            if numLine in addedLinesInBlock:
                output_pattern_value = r"\s*value\s*=\s*"
                if re.search(output_pattern_value, contentLine):
                    return 1
        return 0

    def deletions_contains_value_output_change(self):
        if self.deletions is not None:
            removedLinesInBlock = self.deletions.get_deleted_lines_in_a_block()
            for numLine, contentLine in self.deletions.deleted_lines_content:
                if numLine in removedLinesInBlock:
                    version_pattern = r"\s*value\s*=\s*"
                    if re.search(version_pattern, contentLine):
                        return 1
        return 0
