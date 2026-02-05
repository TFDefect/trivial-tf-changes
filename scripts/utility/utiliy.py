import re


class UtilityChange:

    def __init__(self, bug_inducing_commits=None):
        self.bug_inducing_commits = bug_inducing_commits

    # TODO: Add if the change [addition, deletion] does not concern:
    #   - empty line // only whitespace
    #   - comment
    def exclude_special_lines(self, added_lines):
        result = []
        inside_multi_line_comment = False
        inside_heredoc = False
        heredoc_end_token = None

        for line in added_lines:
            stripped_line = line[1].strip()

            # Detect start of heredoc for description
            heredoc_start_match = re.match(r'description\s*=\s*<<-?\s*([A-Z_]+)', stripped_line)
            if heredoc_start_match:
                inside_heredoc = True
                heredoc_end_token = heredoc_start_match.group(1)
                continue

            # Detect end of heredoc
            if inside_heredoc and stripped_line == heredoc_end_token:
                inside_heredoc = False
                heredoc_end_token = None
                continue

            # Skip lines inside the heredoc, including any changes within it
            if inside_heredoc:
                continue

            # Exclude empty lines
            if not stripped_line:
                continue

            # Check if the line-concern description LINES
            if self.check_description(stripped_line):
                continue

            # Ignore single-line comments in the same line
            if stripped_line.startswith('/*') and stripped_line.endswith('*/'):
                continue

            if stripped_line.startswith('/*') and not stripped_line.endswith('*/'):
                inside_multi_line_comment = True
                continue

            if inside_multi_line_comment:
                continue

            if inside_multi_line_comment and stripped_line.endswith('*/'):
                inside_multi_line_comment = False
                continue

            if stripped_line.startswith(('#', '//')):
                continue

            # Add the line that does not concern:
            # -> description change = "..."
            # -> empty line
            # -> comments :
            #    -> #,
            #    -> /*....*/,
            #    -> //,
            #    -> /* ....\n .....\n  .....\n ......\n */

            result.append(line)

        return result

    def check_description(self, contentLine):
        description_pattern = r'\s*description\s*=\s*"([^"]*)"|\s*description\s*=\s*""'
        if re.search(description_pattern, contentLine):
            return 1

    def identify_inducing_lines(self, tuple_to_search):

        matched_row = self.bug_inducing_commits.loc[
            self.bug_inducing_commits[['bic_file', 'bic_candidate']]
            # self.bug_inducing_commits[['impacted_file', 'bic_candidate']]
            .apply(tuple, axis=1) == tuple_to_search]

        inducing_lines = matched_row['bic_modified_lines']

        if len(inducing_lines):
            return inducing_lines.values[0]

        return []
