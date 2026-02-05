import shlex
from collections import Counter
import math
from pydriller import ModifiedFile
# Updated imports for new location
from scripts.utility.utiliy import UtilityChange
from scripts.utility.filter_values import filter_values_between_start_end


class Additions:

    def __init__(self, mod: ModifiedFile, start=0, end=0):
        self.mod = mod
        self.start = start
        self.end = end
        self.utility = UtilityChange()
        # Exclude @@ empty-lines, @@ comments
        self.added_lines_content = self.utility.exclude_special_lines(self.mod.diff_parsed['added'])
        self.added_lines = [added[0] for added in self.added_lines_content]

    def get_added_lines_in_a_file(self):
        return self.added_lines

    def get_added_lines_content_in_a_file(self):
        return self.added_lines_content

    def get_added_lines_in_a_block(self):
        return filter_values_between_start_end(self.added_lines, self.start, self.end)

    def count_added_lines_in_a_block(self):
        return len(self.get_added_lines_in_a_block())
