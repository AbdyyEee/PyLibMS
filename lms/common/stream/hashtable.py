from lms.fileio.io import FileReader, FileWriter


def read_labels(reader: FileReader) -> tuple[dict, int]:
    labels = {}

    data_start = reader.tell()
    slot_count = reader.read_uint32()
    for _ in range(slot_count):
        label_count = reader.read_uint32()
        offset = reader.read_uint32()
        next_offset = reader.tell()

        reader.seek(data_start + offset)
        for _ in range(label_count):
            length = reader.read_uint8()
            label = reader.read_string_len(length)
            item_index = reader.read_uint32()
            labels[item_index] = label

        reader.seek(next_offset)

    sorted_labels = {i: labels[i] for i in sorted(labels)}

    # While the slot count is consistent for most files, some vary them.
    # Return the slot count to ensure that this change can be recorded.
    return sorted_labels, slot_count


def write_labels(
    writer: FileWriter,
    labels: list[str],
    slot_count: int,
    index_map: dict[str, int] = None,
) -> None:
    writer.write_uint32(slot_count)

    hash_slots = {}

    add_indices = index_map is None

    if index_map is None:
        index_map = {}

    for i, label in enumerate(labels):
        slot = _calculate_hash(label, slot_count)

        hash_slots.setdefault(slot, []).append(label)

        if add_indices:
            index_map[label] = i

    label_offsets = slot_count * 8 + 4

    hash_slots = dict(sorted(hash_slots.items(), key=lambda x: x[0]))

    for i in range(slot_count):
        if i in hash_slots:
            writer.write_uint32(len(hash_slots[i]))
            writer.write_uint32(label_offsets)
            for label in hash_slots[i]:
                label_offsets += len(label) + 5
        else:
            writer.write_uint32(0)
            writer.write_uint32(label_offsets)

    # Write the labels
    for key in hash_slots:
        stored_labels = hash_slots[key]
        for label in stored_labels:
            writer.write_uint8(len(label))
            writer.write_string(label)
            writer.write_uint32(index_map[label])


def _calculate_hash(label: str, slot_count: int) -> int:
    """
    Calucate the hash of a label

    :param label: the label to calculate the hash for.
    :param slot_count: the number of slots.

    Taken directly from https://nintendo-formats.com/libs/lms/overview.html#hash-tables
    """
    hash = 0
    for character in label:
        hash = hash * 0x492 + ord(character)
    return (hash & 0xFFFFFFFF) % slot_count
