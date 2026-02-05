from typing import List
from pydriller import ModifiedFile
# Updated imports for new location
from scripts.utility.utiliy import UtilityChange
from scripts.utility.filter_values import filter_values_between_start_end


class Deletions:

    def __init__(self, mod: ModifiedFile, start=0, end=0):
        self.mod = mod
        self.start = start
        self.end = end
        self.utility = UtilityChange()
        self.deleted_lines_content = self.utility.exclude_special_lines(self.mod.diff_parsed['deleted'])
        self.deleted_lines = [deleted[0] for deleted in self.deleted_lines_content]

    def get_deleted_lines_in_a_file(self) -> List[int]:
        return self.deleted_lines

    def get_deleted_lines_content_in_a_file(self):
        return self.deleted_lines_content

    def get_deleted_lines_in_a_block(self):
        return filter_values_between_start_end(self.deleted_lines, self.start, self.end)

    def count_deleted_lines_in_a_block(self):
        return len(self.get_deleted_lines_in_a_block())
