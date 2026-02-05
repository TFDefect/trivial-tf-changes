import re

class MetaArgsChange:

    def __init__(self, additions, deletions):
        self.additions = additions
        self.deletions = deletions


    def additions_contains_meta_arguments_change(self):
        addedLinesInBlock = self.additions.get_added_lines_in_a_block()
        keywords = ["depends_on", "count", "for_each", "provider", "lifecycle", "provisioner", "connection"]

        for numLine, contentLine in self.additions.added_lines_content:
            if numLine in addedLinesInBlock:
                for keyword in keywords:
                    if re.search(rf"\s*{keyword}\s*", contentLine):
                        return 1
        return 0

    def deletions_contains_meta_arguments_change(self):
        if self.deletions is not None:
            removedLinesInBlock = self.deletions.get_deleted_lines_in_a_block()
            keywords = ["depends_on", "count", "for_each", "provider", "lifecycle", "provisioner", "connection"]
            for numLine, contentLine in self.deletions.deleted_lines_content:
                if numLine in removedLinesInBlock:
                    for keyword in keywords:
                        if re.search(rf"\s*{keyword}\s*", contentLine):
                            return 1
        return 0
