from scripts.process.attr_terraform_change.description_attr_change import DescriptionAttrChange
from scripts.process.attr_terraform_change.default_change import DefaultAttrChange
from scripts.process.attr_terraform_change.meta_arg_change import MetaArgsChange
from scripts.process.attr_terraform_change.type_change import TypeAttrChange
from scripts.process.attr_terraform_change.value_change import ValueAttrChange
from scripts.process.attr_terraform_change.version_change import VersionChange
from scripts.process.lines_change.additions import Additions
from scripts.process.lines_change.deletions import Deletions


class AttrChange:

    def __init__(self, block, additions: Additions, deletions: Deletions):
        self.block = block
        self.additions = additions
        self.deletions = deletions

    def resume_changed_attr(self):
        # isVar = self.block["isVariable"]
        # isOutput = self.block["isOutput"]

        defaultAttrChange = DefaultAttrChange(self.additions, self.deletions)
        typeAttrChange = TypeAttrChange(self.additions, self.deletions)
        valueChange = ValueAttrChange(self.additions, self.deletions)
        versionChange = VersionChange(self.additions, self.deletions)
        descriptionChange = DescriptionAttrChange(self.additions, self.deletions)
        metaArgsChange = MetaArgsChange(self.additions, self.deletions)

        return {
            "additions_contains_default_change": defaultAttrChange.additions_contains_default_change(),
            "deletions_contains_default_change": defaultAttrChange.deletions_contains_default_change(),
            # Type Change
            "additions_contains_type_change": typeAttrChange.additions_contains_type_change(),
            "deletions_contains_type_change": typeAttrChange.deletions_contains_type_change(),
            # Value
            "additions_contains_value_output_change": valueChange.additions_contains_value_output_change(),
            "deletions_contains_value_output_change": valueChange.deletions_contains_value_output_change(),
            # Versioning
            "additions_contains_versioning_change": versionChange.additions_contains_versioning_change(),
            "deletions_contains_versioning_change": versionChange.deletions_contains_versioning_change(),
            # Description
            "additions_contains_description_change": descriptionChange.additions_contains_description_change(),
            "deletions_contains_description_change": descriptionChange.deletions_contains_description_change(),
            # Meta Args
            "additions_contains_meta_args_change": metaArgsChange.additions_contains_meta_arguments_change(),
            "deletions_contains_meta_args_change": metaArgsChange.deletions_contains_meta_arguments_change(),
        }

    @staticmethod
    def get_headers():
        return [
            "additions_contains_default_change", "deletions_contains_default_change",
            "additions_contains_type_change", "deletions_contains_type_change",
            "additions_contains_value_output_change", "deletions_contains_value_output_change",
            "additions_contains_versioning_change", "deletions_contains_versioning_change",
            "additions_contains_description_change", "deletions_contains_description_change",
            "additions_contains_meta_args_change", "deletions_contains_meta_args_change",
        ]
