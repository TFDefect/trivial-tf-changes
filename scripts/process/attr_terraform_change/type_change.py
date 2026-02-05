import re


class TypeAttrChange:

    def __init__(self, additions, deletions):
        self.additions = additions
        self.deletions = deletions

    def additions_contains_type_change(self):
        addedLinesInBlock = self.additions.get_added_lines_in_a_block()
        for numLine, contentLine in self.additions.added_lines_content:
            if numLine in addedLinesInBlock:
                version_pattern = r"\s*type\s*=\s*"
                if re.search(version_pattern, contentLine):
                    return 1
        return 0

    def deletions_contains_type_change(self):
        if self.deletions is not None:
            removedLinesInBlock = self.deletions.get_deleted_lines_in_a_block()
            for numLine, contentLine in self.deletions.deleted_lines_content:
                if numLine in removedLinesInBlock:
                    version_pattern = r'\s*type\s*=\s*'
                    if re.search(version_pattern, contentLine):
                        return 1
        return 0
