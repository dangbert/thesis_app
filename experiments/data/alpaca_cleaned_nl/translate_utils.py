import re
import docx
import config

logger = config.get_logger(__name__, level="INFO")


def serialize_sample(data: dict) -> str:
    """
    Convert a dictionary into a custom string format as specified.
    """
    serialized_str = f"<==={data['orig_index']}===>\n"
    serialized_str += f"<===output===>{data['output']}</===output===>\n"
    serialized_str += f"<===input===>{data.get('input', '')}</===input===>\n"
    serialized_str += f"<===instruction===>{data['instruction']}</===instruction===>\n"
    serialized_str += f"</==={data['orig_index']}===>"
    return serialized_str


PATTERN_EXP = r"<===(\d+)===>\n<===output===>(.*?)</===output===>\n<===input===>(.*?)</===input===>\n<===instruction===>(.*?)</===instruction===>\n</===\1===>"


def deserialize_sample(data_str: str) -> dict:
    """
    Convert the custom string format back into a dictionary.
    """
    import re

    match = re.match(PATTERN_EXP, data_str, re.DOTALL)
    if match:
        orig_index, output, input_str, instruction = match.groups()
        return {
            "orig_index": int(orig_index),
            "output": output.strip(),
            "input": input_str.strip(),
            "instruction": instruction.strip(),
        }
    raise ValueError("String does not match the expected format")


def serialize_dataset(dataset, fname: str, assert_sanity: bool = False):
    """Serialize dataset to a text file or a Word (.docx) document."""
    bad_count = 0

    def process_item(item: dict):
        nonlocal bad_count
        cereal = serialize_sample(item)
        if not deserialize_sample(cereal) == item:
            bad_count += 1
            if assert_sanity:
                assert deserialize_sample(cereal) == item
        return cereal

    if fname.endswith(".docx"):
        document = docx.Document()
        for item in dataset:
            cereal = process_item(item)
            document.add_paragraph(cereal)
        document.save(fname)

    else:
        with open(fname, "w") as f:
            for item in dataset:
                cereal = process_item(item)
                f.write(cereal + "\n")

    if bad_count > 0:
        logger.warning(
            f"Failed to perfectly encode: {bad_count}/{len(dataset)} samples"
        )


def deserialize_dataset(fname: str) -> list[dict]:
    """Deserialize dataset from a text or Word (.docx) file using pattern matching."""
    dataset = []
    if fname.lower().endswith(".docx"):
        logger.info(f"loading dataset from a Word document: '{fname}'")
        document = docx.Document(fname)
        data_str = "\n".join([p.text for p in document.paragraphs])
    else:
        logger.info("loading dataset from a text file: '{fname}'")
        with open(fname, "r") as f:
            data_str = f.read()

    pattern = re.compile(PATTERN_EXP, re.DOTALL)
    matches = pattern.finditer(data_str)
    for match in matches:
        serialized_sample = match.group(0)  # Extract the entire matched sample block
        deserialized_dict = deserialize_sample(serialized_sample)
        dataset.append(deserialized_dict)

    return dataset
