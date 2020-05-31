import json


class FrontMatterParser:

    # Returns boolean indicating if the text contains front matter
    @staticmethod
    def contains_frontmatter(raw_text):
        lines = raw_text.split("\n")
        text_contains_fences = lines[0].startswith("---") and (len([line for line in lines if line.startswith("---")]) >= 2)
        contains_frontmatter_type = not lines[0].endswith("---")
        return text_contains_fences and contains_frontmatter_type
    
    @staticmethod
    def can_parse(frontmatter_type):
        return get_parsers().get(frontmatter_type) is not None

    @staticmethod
    def get_frontmatter_type(raw_text):
        lines = raw_text.split("\n")
        return lines[0].lstrip("-")
    
    # Returns frontmatter without fences
    @staticmethod
    def get_frontmatter(raw_text):
        front_matter = raw_text.split("---\n")[0].rstrip("\n")
        lines = front_matter.split("\n")
        return "\n".join(lines[1:])

    # Returns boolean indicating if the text contains valid front matter
    @classmethod
    def validate_text(cls, raw_text):
        if cls.contains_frontmatter(raw_text):
            frontmatter_type = cls.get_frontmatter_type(raw_text)
            return cls.can_parse(frontmatter_type)
        return False
    
    # Parses raw text and returns dictionary containing front matter data
    @classmethod
    def parse_text(cls, raw_text):
        if cls.validate_text(raw_text):
            frontmatter_type = raw_text.split("\n")[0].lstrip("-")
            frontmatter_content = cls.get_frontmatter(raw_text)
            parser = get_parsers().get(frontmatter_type)
            return parser(frontmatter_content)
        else: 
            raise ValueError("Invalid frontmatter")

    # Loads file and returns dictionary containing front matter data
    @classmethod
    def parse_file(cls, filepath):
        with open(filepath, 'r', encoding="utf-8") as f:
            return cls.parse_text(f.read())

    # Loads file and returns and returns content and frontmatter separately
    @classmethod
    def load_file(cls, filepath):
        with open(filepath, 'r', encoding="utf-8") as f:
            raw_text = f.read()
        
        if cls.contains_frontmatter(raw_text):
            split_text = raw_text.split("---\n")
            content = "".join(split_text[1:])
            frontmatter_type = cls.get_frontmatter_type(raw_text)

            if cls.can_parse(frontmatter_type):
                return content, cls.parse_text(raw_text)
            else:
                return content, {}
        else:
            return raw_text, {}

    @staticmethod
    def save(data, output_file):
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(str(key) + ": " + "[" + ",".join(value) + "]")
            else:
                lines.append(str(key) + ": " +  str(value))

        with open(output_file, 'w', encoding="utf-8") as f:
            f.write("\n".join(lines))

# Parser for page front matter
#    * Simple key/value pairings
#    * Comma-separated lists between brackets
#    * Keys are case insensitive
def parseSimpleFrontMatter(raw_text):
    front_matter = {}
    lines = raw_text.split("\n")
    for line in lines:
        if ":" in line:
            key, value = (item.strip() for item in line.split(": "))
            if value.startswith("[") and value.endswith("]"):
                value = [item.strip() for item in value[1:-1].split(",")]
            front_matter[key.lower()] = value
        else:
            continue
    return front_matter

def parseJSON(raw_text):
    return json.loads(raw_text)

def get_parsers():
    return {
        "simple": parseSimpleFrontMatter,
        "json": parseJSON
    }