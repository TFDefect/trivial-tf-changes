# from scripts.block_locator.block_identificator import BlockIdentificator
from scripts.edits.distance import Distance


class SimilarityChange():

    def __init__(self, currentBlock, pathAfterChange, OldestBlock, pathBeforeChange):
        # self.blockIdentificator = BlockIdentificator()
        self.currentBlock = currentBlock
        self.OldestBlock = OldestBlock
        self.pathAfterChange = pathAfterChange
        self.pathBeforeChange = pathBeforeChange

    def _read_block_from_file(self, file_path, start_line, end_line):
        if not file_path or start_line is None or end_line is None:
            return ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Adjust for 1-based indexing, careful with bounds
                start_idx = max(0, start_line - 1)
                end_idx = min(len(lines), end_line)
                return "".join(lines[start_idx:end_idx])
        except Exception:
            return ""

    def identify_blocks_before_after_change_as_str(self):
        # Get the content of block that changed before
        strBeforeChange: str = ""
        strAfterChange: str = ""
        if self.OldestBlock is not None:
            strBeforeChange = self._read_block_from_file(
                self.pathBeforeChange,
                self.OldestBlock.get("start_block"),
                self.OldestBlock.get("end_block")
            )

        # Get the content of block that recently changed
        strAfterChange = self._read_block_from_file(
            self.pathAfterChange,
            self.currentBlock.get("start_block"),
            self.currentBlock.get("end_block")
        )
        return strBeforeChange, strAfterChange

    def resume_similarity_change(self):
        strBeforeChange, strAfterChange = self.identify_blocks_before_after_change_as_str()
        # We should remove WhiteSpace,
        # and Comment before comparing that
        distance_for_code_change = Distance(strBeforeChange, strAfterChange)
        return {
            "damerau_levenshtein_code_change_distance": distance_for_code_change.measure_damerau_levenshtein_distance()}
    @staticmethod
    def get_headers():
        return ["damerau_levenshtein_code_change_distance"]
