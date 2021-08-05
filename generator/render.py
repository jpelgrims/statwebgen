import os
import markdown

from jinja2 import Template, Environment, FileSystemLoader
from markdown.extensions.toc import TocExtension
from markdown_extensions import AsideExtension


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

def render_markdown(markdown_content: str, metadata: dict, input_dir: str, data: dict = {}) -> str:
    """
    Renders the given markdown into html, using the given metadata and data as template inputs.

    This function used the markdown library, along with the following plugins: 
       * 'codehilite' for code highlighting
       * 'fenced_code' for code block definitions
       * 'toc' for table of contents
       * 'extra' for markdown inside html blocks
    Args:
        markdown_content (str): A string containing markdown
        metadata (dict): Metadata associated with the markdown
        input_dir (str): Folder that is being converted
        data (dict): Random data to be used in the templates

    Returns:
        str: A string containing the render result in HTML
    """
    md = markdown.Markdown(extensions=[AsideExtension(), 'fenced_code', TocExtension(baselevel=1), 'extra', 'wikilinks'])
    template_path = os.path.join(input_dir, ".templates", metadata.get("template", ""))
    
    if not os.path.exists(template_path) or not os.path.isfile(template_path):
        template_path = os.path.join(SCRIPT_DIR, "templates", "default.html")

    with open(template_path, encoding="utf-8") as f:
        template = Environment(loader=FileSystemLoader(os.path.join(input_dir, ".templates"))).from_string(f.read())

    rendered_content = Template(markdown_content).render(data=data)
    html_content = md.convert(rendered_content)

    return template.render(content=html_content,
                            toc=md.toc, 
                                metadata=metadata,
                                data=data)


def save_render(rendered_content: str, filepath: str):
    """
    Saves the given content in a file with the given filepath. If folder structure for the
    file path does not exist, it will be created.

    Args:
        rendered_content (str): Content to be saved.
        filepath (str): Filepath where the content will be saved.
    """
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with open(filepath, 'w', encoding="utf-8") as file:
        file.write(rendered_content) 