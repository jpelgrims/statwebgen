import os
import os.path
import glob
import time
import sys
import shutil
import threading
from queue import Queue
from datetime import datetime
from enum import Enum

from parsing import load_markdown_file
from render import render_markdown, save_render
from config import get_config


class FileState(Enum):
    Deleted = 0
    Added = 1

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

def scan(directory: str, pattern: str = "*", exclude_dirs: [str] = [], include_templates: bool = False) -> [str]:
    files = []
    for dir,_,_ in os.walk(directory):
        files.extend(glob.glob(os.path.join(dir,pattern)))
        
    files = [
        file for file in files if \
            not any(dir in file for dir in exclude_dirs) and \
            not any(part.startswith(".") for part in file.split(os.path.sep)) and \
            not os.path.isdir(file)
    ]

    if include_templates:
        files.extend(glob.glob(os.path.join(directory,".templates", "*.html")))
        
    return files

def scan_threaded(change_queue: Queue, directory: str, pattern: str = "*", exclude_dirs: [str] = [], include_templates: bool = False) -> [str]:
    """
    Scans the provided directory for any files that are required for the static website build.

    Args:
        folder (str): Directory to be scanned   
        pattern (str, optional): Pattern that is used for scannign the given directory. Defaults to "*".
        exclude_dirs ([str]): List of directories not to be included in the scan. 
        include_templates (bool, optional): Whether to include the templates or not. Defaults to False.

    Returns:
        [str]: List of files in the directory, with filepaths starting from the provided directory.
    """
    filelist = []
    while True:
        new_filelist = scan(directory, pattern, exclude_dirs, include_templates)
        
        added_files = [file for file in new_filelist if not file in filelist]
        removed_files = [file for file in filelist if not file in new_filelist]

        for file in removed_files:
            change_queue.put({
                "type": FileState.Deleted,
                "filepath": file 
            })
        
        for file in added_files:
            change_queue.put({
                "type": FileState.Added,
                "filepath": file 
            })
        
        filelist = new_filelist

        time.sleep(1)


def derive_output_path(input_path, input_dir, output_dir):
    output_path = os.path.join(output_dir, os.path.relpath(input_path, input_dir))

    if output_path.endswith(".md"):
        output_path = output_path.replace(".md", ".html")
    return output_path




def build_website(args):
    files = scan(args.input_dir)
    process_files(files, args.input_dir, args.output_dir, args.draft)

# Check for modified files and only rebuild those
def autobuild_website(args, kill_switch):
    change_queue = Queue()

    # The scanner finds newly added or deleted files. It is a thread because the 
    # scanning operation is quite costly, and I can't be bothered to speed it up.
    scanner = threading.Thread(target=scan_threaded, args=(change_queue, args.input_dir, "*", [], True,), daemon=True)
    scanner.start()

    files = []
    last_modified = {}
    while not kill_switch.is_set():
        file_changes = []
        while not change_queue.empty():
            file_changes.append(change_queue.get())
        
        change_count = len(file_changes)
        if change_count > 0:
            print(f"{change_count} files were added and/or removed")

        for change in file_changes:
            type = change.get("type")
            filepath = change.get("filepath")

            if type == FileState.Deleted:
                files.remove(filepath)
            elif type == FileState.Added:
                files.append(filepath)
        
        modified_files = []
        for file in files:
            stat = None
            try:
                stat = os.stat(file)
            except FileNotFoundError as e:
                continue

            if file not in last_modified.keys():
                # File added since last scan
                modified_files.append(file)
                last_modified[file] = stat[8]
            elif last_modified[file] < stat[8]:
                # File modified since last scan
                modified_files.append(file)
                last_modified[file] = stat[8]

        # Look for changed templates
        build_files = []
        for file in modified_files:
            if file.endswith(".html"):

                # Find all md files that use the changed template
                md_files = [f for f in files if ".md" in f]
                for md_file in md_files:
                    content, metadata = load_markdown_file(md_file)

                    if metadata.get("template", None) == os.path.basename(file):
                        build_files.append(md_file)
            else:
                build_files.append(file)

        if len(build_files) > 0:
            print("{} file(s) modified, rebuilding...\n".format(len(build_files)))
            process_files(build_files, args.input_dir, args.output_dir, args.draft)
        time.sleep(0.01)
    print("Shutting down autobuild process...")
    sys.exit(0)


def post_process_render(html: str, metadata, config) -> str:
    head_additions = []

    for script in metadata.get('scripts') or []:
        script_element = f"<script type='text/javascript' async src='/{config['resourceFolders']['js']}{script}'></script>"
        head_additions.append(script_element)

    for stylesheet in metadata.get('stylesheets') or []:
        style_element = f"<link rel='stylesheet' type='text/css' href='/{config['resourceFolders']['css']}{stylesheet}'>"
        head_additions.append(style_element)

    # Insert head additions
    head_additions = "\n".join(["\t" + addition for addition in head_additions]) + "\n"
    index = html.find("</head>")

    html = html[:index] + head_additions + html[index:]
    return html


def generate_directory_structure(files, input_dir):
    directory_structure = {}
    for file in files:
        relative_path = os.path.relpath(file, input_dir)
        directory = os.path.dirname(relative_path)
        
        if directory == "":
            continue

        path_parts = directory.split(os.path.sep)

        structure = directory_structure
        for i in range(len(path_parts)):
            part = path_parts[i]
            if part not in structure:
                structure[part] = {}
            structure = structure[part]
    return directory_structure

def process_files(files: [str], input_dir: str, output_dir: str, drafts: bool = False):
    project_files = {}
    otherr_files = {}

    directory_structure = generate_directory_structure(files, input_dir)
    config = get_config(input_dir)
    
    # Sort files into markdown and other
    md_files = [file for file in files if ".md" in file]
    other_files = [file for file in files if not ".md" in file]

    # Copy other files to output directory, we do not need to process these
    for file in other_files:
        output_path = derive_output_path(file, input_dir, output_dir)
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        shutil.copyfile(file, output_path)

        otherr_files[file] = {
            "link": os.path.relpath(file, input_dir)
        }
    
    # Parse metadata of all files
    for md_file in md_files:
        content, metadata = load_markdown_file(md_file)

        if not drafts and metadata.get('draft') == "true":
            continue

        if metadata.get('published'):
            metadata['published'] = datetime.strptime(metadata['published'], "%d/%m/%Y").strftime("%Y-%m-%d")

        project_files[md_file] = metadata
        project_files[md_file]["path"] = md_file
        project_files[md_file]["filename"] = os.path.basename(md_file)
        project_files[md_file]["link"] = os.path.relpath(md_file, input_dir).replace(".md", "")

    # Process markdown files
    for md_file in md_files:
        if not drafts and project_files.get(md_file, {}).get('draft') == "true":
            continue

        content, metadata = load_markdown_file(md_file)
        render = render_markdown(content, metadata, input_dir, data={"files": project_files, "other_files": otherr_files, "directory_structure": directory_structure})
        render = post_process_render(render, metadata, config)
        save_render(render, derive_output_path(md_file, input_dir, output_dir))