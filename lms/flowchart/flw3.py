from lms.common.field.io import read_field, write_field
from lms.common.field.lms_datatype import LMS_DataType
from lms.common.field.lms_field import LMS_FieldMap, LMS_Field
from lms.common.lms_exceptions import LMS_Error
from lms.fileio.io import FileReader, FileWriter
from lms.flowchart.definitions.node import (
    LMS_MessageNode,
    LMS_EntryNode,
    LMS_BranchNode,
    LMS_EventNode,
    LMS_JumpNode,
    LMS_BaseNode,
    LMS_NodeParameter,
)
from lms.flowchart.definitions.node_type import LMS_NodeType, LMS_NodeParameterType
from lms.message.msbt import MSBT
from lms.titleconfig.definitions.nodes import NodeConfig, NodeDefinition

NO_NEXT_NODE = 0xFFFF
FLW3_HEADER_SIZE = 16
NODE_SIZE = 16

VARIABLE_WIDTH_DATATYPES = (LMS_DataType.BOOL, LMS_DataType.LIST)


def read_flw3(
    reader: FileReader,
    config: NodeConfig | None,
    msbt: MSBT | None,
) -> tuple[int, dict[int, LMS_EntryNode]]:
    section_start = reader.tell()
    node_count = reader.read_uint16()
    branch_table_id_count = reader.read_uint16()

    # Huge padding section skip
    reader.skip(12)

    nodes: list[LMS_BaseNode] = []
    entry_nodes: list[LMS_EntryNode] = []

    next_id_map: dict[LMS_BaseNode, int | None] = {}
    branch_metadata: dict[LMS_BranchNode, dict] = {}

    for i in range(node_count):
        node_data = reader.tell() + 8
        node_type = LMS_NodeType(reader.read_uint8())
        parameter_type = LMS_NodeParameterType(reader.read_int8())

        reader.skip(2)

        parameter_offset = reader.tell()
        match node_type:
            case LMS_NodeType.MESSAGE:
                reader.skip(4)

                stream_next_id = read_next_node_id(reader)
                file_index = reader.read_uint16()
                message_index = reader.read_uint16()
                node = LMS_MessageNode(i, file_index, message_index, msbt)
                reader.skip(2)
            case LMS_NodeType.BRANCH:
                # There is no next node id as the next node is determined by the branches
                # Skip parameter value alongside that
                reader.skip(2 + 4)

                condition_id = reader.read_uint16()
                case_count = reader.read_uint16()
                table_index = reader.read_uint16()
                end = reader.tell()

                reader.seek(parameter_offset)
                definition = get_config_definition(
                    config, LMS_NodeType.BRANCH, parameter_type, condition_id
                )
                parameter_value = evaluate_node_parameter(
                    reader, section_start, parameter_type, definition
                )

                node = LMS_BranchNode(
                    i, parameter_type, parameter_value, condition_id, definition
                )

                # Save the metadata for the branch node so that the branches itself can be set later on
                branch_metadata[node] = case_count, table_index
                reader.seek(end)
            case LMS_NodeType.EVENT:
                reader.skip(4)

                stream_next_id = read_next_node_id(reader)
                event_id = reader.read_uint16()
                end = reader.tell() + 4

                reader.seek(parameter_offset)

                definition = get_config_definition(
                    config, LMS_NodeType.EVENT, parameter_type, event_id
                )
                parameter_value = evaluate_node_parameter(
                    reader, section_start, parameter_type, definition
                )

                node = LMS_EventNode(
                    i, parameter_type, parameter_value, event_id, definition
                )
                reader.seek(end)
            case LMS_NodeType.ENTRY:
                reader.seek(node_data)
                stream_next_id = read_next_node_id(reader)
                node = LMS_EntryNode(i)
                entry_nodes.append(node)
                reader.skip(6)
            case LMS_NodeType.JUMP:
                reader.seek(node_data)
                stream_next_id = read_next_node_id(reader)
                unknown_short0a = reader.read_uint16()
                node = LMS_JumpNode(i, unknown_short0a)
                reader.skip(4)

        next_id_map[node] = stream_next_id
        nodes.append(node)

    node_map: dict[int, LMS_BaseNode] = {node.id: node for node in nodes}
    branch_ids = [read_next_node_id(reader) for _ in range(branch_table_id_count)]

    for node in nodes:
        next_node_id = next_id_map[node]

        if isinstance(node, LMS_BranchNode):
            case_count, starting_index = branch_metadata[node]

            # Slice the portion of IDs linked to this branch node and add the node objects themselves
            for branch_id in branch_ids[starting_index : starting_index + case_count]:
                if branch_id is None:
                    node.add_branch(None)
                else:
                    node.add_branch(node_map[branch_id])

            continue
        elif isinstance(node, LMS_JumpNode):
            node.next_flowchart = node_map[next_node_id]
            continue

        if next_node_id is None:
            continue

        node.set_next_node(node_map[next_node_id])

    return node_count, entry_nodes


def read_next_node_id(reader: FileReader) -> int | None:
    return None if (id := reader.read_uint16()) == NO_NEXT_NODE else id


def get_config_definition(
    config: NodeConfig,
    node_type: LMS_NodeType.BRANCH | LMS_NodeType.EVENT,
    parameter_type: LMS_NodeParameterType,
    id: int,
) -> NodeDefinition:
    return (
        None if config is None else config.get_definition(id, node_type, parameter_type)
    )


def evaluate_node_parameter(
    reader: FileReader,
    section_start: int,
    parameter_type: LMS_NodeParameterType,
    definition: NodeDefinition | None,
) -> LMS_NodeParameter:
    # How functions may utilize node parameters vary, such that they may cast values as they wish.
    # By default, PyLibMS interprets the parameter types using signed integers for simplicity.
    # If the user believes a better interpretation fits, then they may utilize a node configuration
    # and cast individual parameters to any LMS_Datatype.
    # This is my understanding of how node parameters work, but updating may be necessary as more research surfaces.
    if definition is not None:
        result = {}

        if parameter_type is LMS_NodeParameterType.STRING:
            param_definition = definition.parameter_definitions[0]
            value = reader.read_string_offset(section_start)

            return LMS_FieldMap(
                {param_definition.name: LMS_Field(value, param_definition)}
            )

        for i, param_definition in enumerate(definition.parameter_definitions):
            # By default VARIABLE_WIDTH_DATATYPES are allocated a single byte for its index.
            # Some games may utilize a whole 4 byte stack as an index and/or 2 bytes depending on the parameter type.
            stream_map = {
                1: reader.read_uint8,
                2: reader.read_uint16,
                4: reader.read_uint32,
            }
            result[param_definition.name] = read_field(
                reader,
                param_definition,
                stream_map[parameter_type.sliced_datatype[i].stream_size],
            )

        return LMS_FieldMap(result)
    else:
        # Default parameter reading
        match parameter_type:
            case LMS_NodeParameterType.PARAM_32_0 | LMS_NodeParameterType.PARAM_32_1:
                return reader.read_uint32()
            case LMS_NodeParameterType.PARAM_16_16:
                return reader.read_uint16(), reader.read_uint16()
            case LMS_NodeParameterType.PARAM_16_8_8:
                return reader.read_uint16(), reader.read_uint8(), reader.read_uint8()
            case LMS_NodeParameterType.PARAM_8_8_16:
                return reader.read_uint8(), reader.read_uint8(), reader.read_uint16()
            case LMS_NodeParameterType.PARAM_8_8_8_8:
                return (
                    reader.read_uint8(),
                    reader.read_uint8(),
                    reader.read_uint8(),
                    reader.read_uint8(),
                )
            case LMS_NodeParameterType.STRING:
                return reader.read_string_offset(section_start)
            case _:
                raise LMS_Error(f"Invalid parameter type of '{parameter_type}'!")


def write_flw3(
    writer: FileWriter, nodes: list[LMS_BaseNode], stream_ids: dict[LMS_BaseNode, int]
) -> None:
    node_count = len(nodes)

    branch_table: list[int] = []
    string_table: list[str] = []
    string_offsets: list[int] = []

    writer.write_uint16(node_count)
    branch_id_offset = writer.tell()

    # Placeholder value for branch table count
    writer.write_uint16(0)

    writer.write_bytes(b"\x00" * 12)
    for node in nodes:
        writer.write_int8(node.type)
        writer.write_int8(node.parameter_type)

        match node:
            case LMS_MessageNode():
                writer.write_bytes(b"\x00" * 2)
                writer.write_bytes(b"\x00" * 4)

                write_next_node_id(
                    writer,
                    None if node.next_node is None else stream_ids[node.next_node],
                )

                writer.write_uint16(node.msbt_index)
                writer.write_uint16(node.label_index)

                writer.write_bytes(b"\x00\x00")
            case LMS_BranchNode():
                writer.write_bytes(b"\x00\x00")

                if node.parameter_type is LMS_NodeParameterType.STRING:
                    string_offsets.append(writer.tell())

                    if node.definition is not None:
                        parameter_definition = node.definition.parameter_definitions[0]
                        field = node.parameter_value[parameter_definition.name]
                        string_table.append(field.value)
                    else:
                        string_table.append(node.parameter_value)

                    writer.write_uint32(0)
                else:
                    write_node_parameter(
                        writer, node.parameter_value, node.parameter_type
                    )

                starting_index = len(branch_table)
                for branch in node.branches.values():
                    if branch is None:
                        branch_table.append(NO_NEXT_NODE)
                    else:
                        branch_table.append(stream_ids[branch])

                writer.write_uint16(NO_NEXT_NODE)

                writer.write_uint16(node.condition_id)
                writer.write_uint16(node.case_count)
                writer.write_uint16(starting_index)
            case LMS_EventNode():
                writer.write_bytes(b"\x00\x00")

                if node.parameter_type is LMS_NodeParameterType.STRING:
                    string_offsets.append(writer.tell())

                    if isinstance(node.parameter_value, LMS_FieldMap):
                        parameter_definition = node.definition.parameter_definitions[0]
                        field = node.parameter_value[parameter_definition.name]
                        string_table.append(field.value)
                    else:
                        string_table.append(node.parameter_value)

                    writer.write_uint32(0)
                else:
                    write_node_parameter(
                        writer, node.parameter_value, node.parameter_type
                    )

                write_next_node_id(
                    writer,
                    None if node.next_node is None else stream_ids[node.next_node],
                )
                writer.write_uint16(node.event_id)

                writer.write_bytes(b"\x00" * 4)
            case LMS_EntryNode():
                writer.write_bytes(b"\x00" * 2)
                writer.write_bytes(b"\x00" * 4)

                write_next_node_id(
                    writer,
                    None if node.next_node is None else stream_ids[node.next_node],
                )
                writer.skip(6)
            case LMS_JumpNode():
                writer.write_bytes(b"\x00" * 2)
                writer.write_bytes(b"\x00" * 4)

                write_next_node_id(writer, stream_ids[node.next_flowchart])
                writer.write_uint16(node.unknown_short0a)
                writer.skip(4)

    for node_id in branch_table:
        writer.write_uint16(node_id)

    string_offset = (
        FLW3_HEADER_SIZE + (NODE_SIZE * node_count) + (2 * len(branch_table))
    )

    for offset, string in zip(string_offsets, string_table):
        write_offset = writer.tell()

        writer.seek(offset)
        writer.write_uint32(string_offset)

        writer.seek(write_offset)
        writer.write_encoded_string(string)

        string_offset += len(string) * writer.encoding.width + len(
            writer.encoding.terminator
        )

    end = writer.tell()
    writer.seek(branch_id_offset)
    writer.write_uint16(len(branch_table))
    writer.seek(end)


def write_node_parameter(
    writer: FileWriter, value: LMS_NodeParameter, parameter_type: LMS_NodeParameterType
) -> None:
    if isinstance(value, LMS_FieldMap):
        for i, field in enumerate(value):
            # In MSBF files there could be a case where naturally one bit datatypes take up 2/4 bits.
            if field.datatype in VARIABLE_WIDTH_DATATYPES:
                stream_map = {
                    1: writer.write_uint8,
                    2: writer.write_uint16,
                    3: writer.write_uint32,
                }
                write_field(
                    writer,
                    field,
                    stream_map[parameter_type.sliced_datatype[i].stream_size],
                )
            else:
                write_field(writer, field)
        return

    match parameter_type:
        case LMS_NodeParameterType.PARAM_32_0 | LMS_NodeParameterType.PARAM_32_1:
            writer.write_uint32(value)
        case LMS_NodeParameterType.PARAM_16_16:
            writer.write_uint16(value[0])
            writer.write_uint16(value[1])
        case LMS_NodeParameterType.PARAM_16_8_8:
            writer.write_uint16(value[0])
            writer.write_uint8(value[1])
            writer.write_uint8(value[2])
        case LMS_NodeParameterType.PARAM_8_8_16:
            writer.write_uint8(value[0])
            writer.write_uint8(value[1])
            writer.write_uint16(value[2])
        case LMS_NodeParameterType.PARAM_8_8_8_8:
            writer.write_uint8(value[0])
            writer.write_uint8(value[1])
            writer.write_uint8(value[2])
            writer.write_uint8(value[3])


def write_next_node_id(writer: FileWriter, id: int | None) -> None:
    writer.write_uint16(NO_NEXT_NODE if id is None else id)
