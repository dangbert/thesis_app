import re


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
    """Serialize (alpaca) dataset to a text file which can ideally be translated as a single document translation and then deserialized back."""

    with open(fname, "w") as f:
        for i, item in enumerate(dataset):
            cereal = serialize_sample(item)
            if assert_sanity:
                assert deserialize_sample(cereal) == item
            f.write(cereal + "\n")


def deserialize_dataset(fname: str) -> list[dict]:
    """Deserialize dataset from a text file using pattern matching."""
    dataset = []
    with open(fname, "r") as f:
        data_str = f.read()
        pattern = re.compile(PATTERN_EXP, re.DOTALL)

        matches = pattern.finditer(data_str)
        for match in matches:
            serialized_sample = match.group(
                0
            )  # Extract the entire matched sample block
            deserialized_dict = deserialize_sample(serialized_sample)
            dataset.append(deserialized_dict)

    return dataset
