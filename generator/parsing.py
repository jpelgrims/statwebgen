import json


def contains_frontmatter(raw_text):
    lines = raw_text.split("\n")
    text_contains_fences = lines[0].startswith("---") and (len([line for line in lines if line.startswith("---")]) >= 2)
    return text_contains_fences

def load_markdown_file(filepath):
    with open(filepath, 'r', encoding="utf-8") as f:
        raw_text = f.read()
    return parse_markdown(raw_text)

# Loads markdown text and returns content and frontmatter separately
def parse_markdown(raw_text: str) -> (str, dict):
    """
    Parses the given markdown string and separates the frontmatter from the markdown (if any)

    Args:
        raw_text (str): [description]

    Returns:
        (str, dict): A tuple containing the markdown as string and the frontmatter as dict (empty if none)
    """
    if contains_frontmatter(raw_text):
        split_text = raw_text.split("---\n")
        content = "".join(split_text[2:])
        frontmatter = "".join(split_text[:2])
        return content, parse_frontmatter(frontmatter)
    else:
        return raw_text, {}

def save_frontmatter(data: dict) -> str:
    """
    Saves the given dictionary as markdown frontmatter.

    Args:
        data (dict): Dictionary containing all the frontmatter key-value pairs

    Returns:
        str: A string containing the frontmatter in the correct plaintext format 
    """
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(str(key) + ": " + "[" + ",".join([f"'{x}'" for x in value]) + "]")
        else:
            lines.append(str(key) + ": " +  str(value))
    return "\n".join(lines)

def parse_frontmatter(raw_text: str) -> dict:
    """
    Parser for markdown file front matter. This parser has the following features:
       * Simple key-value pairings (`key: value`)
       * Comma-separated lists between brackets (`list: ['value1', 'value2']`)
       * Keys are case insensitive

    Args:
        raw_text (str): String containing frontmatter (excluding fences)

    Returns:
        dict: A dictionary containing all the frontmatter key:value pairs
    """
    front_matter = {}
    lines = raw_text.split("\n")
    for line in lines:
        if ":" in line:
            key, value = (item.strip() for item in line.split(": "))
            if value.startswith("[") and value.endswith("]"):
                value = [item.strip().strip("'\"") for item in value[1:-1].split(",")]
            front_matter[key.lower()] = value
        else:
            continue
    return front_matter