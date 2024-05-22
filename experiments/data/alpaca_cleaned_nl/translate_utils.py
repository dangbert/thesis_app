def serialize(data: dict) -> str:
    """
    Convert a dictionary into a custom string format as specified.
    """
    serialized_str = f"<==={data['orig_index']}===>\n"
    serialized_str += f"<===output===>{data['output']}</===output===>\n"
    serialized_str += f"<===input===>{data.get('input', '')}</===input===>\n"
    serialized_str += f"<===instruction===>{data['instruction']}</===instruction===>\n"
    serialized_str += f"</==={data['orig_index']}===>"
    return serialized_str


def deserialize(data_str: str) -> dict:
    """
    Convert the custom string format back into a dictionary.
    """
    import re

    pattern = r"<===(\d+)===>\n<===output===>(.*?)</===output===>\n<===input===>(.*?)</===input===>\n<===instruction===>(.*?)</===instruction===>\n</===\1===>"
    match = re.match(pattern, data_str, re.DOTALL)
    if match:
        orig_index, output, input_str, instruction = match.groups()
        return {
            "orig_index": int(orig_index),
            "output": output.strip(),
            "input": input_str.strip(),
            "instruction": instruction.strip(),
        }
    raise ValueError("String does not match the expected format")
