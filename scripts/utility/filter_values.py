from typing import List


def filter_values_between_start_end(values: List[int], start: int, end: int):
    return [value for value in values if start < value < end]


def clean_similar_blocks_in_commit(impacted_blocks, attributes, target_label):
    # Create a set to track unique first three attributes
    unique_attributes = set()
    unique_blocks = []
    duplicated_blocks = []
    overlap = 0

    # for block in impacted_blocks:
    #     counter = 0
    #     for iter in iterations:
    #         if block["block_identifiers"] == iter["block_identifiers"] and block["file"] == iter["file"]:
    #             counter += 1
    #     block["num_change_before"] = counter

    # Process each dictionary in the list
    for block in impacted_blocks:
        first_three = extract_first_three_attributes_from_dict(block, attributes)
        if first_three not in unique_attributes:
            unique_attributes.add(first_three)
            unique_blocks.append(block)
        else:
            idx = [idx for idx, b in enumerate(unique_blocks) if
                   extract_first_three_attributes_from_dict(b, attributes) == first_three][0]
            duplicated_blocks.append(block)
            if unique_blocks[idx] not in duplicated_blocks:
                duplicated_blocks.append(unique_blocks[idx])

            if block[target_label] == 1 and unique_blocks[idx][target_label] == 0:
                unique_blocks[idx] = block
                overlap = 1
    return unique_blocks, duplicated_blocks, overlap


def clean_similar_blocks_among_commits(iterations, clean_blocks, attributes):
    light_weight_current_blocks = [extract_first_three_attributes_from_dict(clean, attributes) for clean in
                                   clean_blocks]
    light_weight_ancient_blocks = [extract_first_three_attributes_from_dict(block, attributes) for block in iterations]
    more_cleanable_blocks = []
    for idx, current in enumerate(light_weight_current_blocks):
        if current not in light_weight_ancient_blocks:
            more_cleanable_blocks.append(clean_blocks[idx])
    return more_cleanable_blocks


def extract_first_three_attributes_from_dict(block, attributes):
    return tuple(block[attr] for attr in attributes)
