import os
import os.path
import sys
import shutil
from distutils.dir_util import copy_tree
import glob
import time
import threading
import socket

import json
import markdown
import argparse

from markdown_extensions import AsideExtension
from markdown.extensions.toc import TocExtension
from parsing import FrontMatterParser
from jinja2 import Template

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


class Website:

    def __init__(self, input_dir, output_dir=None):
        self.input_dir = input_dir

        if not output_dir:
            self.output_dir = os.path.join(self.input_dir, ".build")
        else:
            self.output_dir = output_dir
        
        self.exclude_dir = [f.name for f in os.scandir(self.input_dir) if f.is_dir() and f.name.startswith(".")]

    # Only if github pages website
    def publish(self, message):
        os.chdir(self.output_dir)
        os.system('git add --all')
        os.system('git commit -m "{}"'.format(message))
        os.system('git push')

    def _scan(self, pattern="*", include_templates=False):
        files = []
        pattern   = pattern

        for dir,_,_ in os.walk(self.input_dir):
            files.extend(glob.glob(os.path.join(dir,pattern)))
        
        files = [file for file in files if not any(dir in file for dir in self.exclude_dir) and not os.path.isdir(file) ]

        if include_templates:
            files.extend(glob.glob(os.path.join(self.input_dir,".templates", "*.html")))

        return files

    def _get_output_path(self, input_path):
        output_path = os.path.join(self.output_dir, os.path.relpath(input_path, self.input_dir))

        if output_path.endswith(".md"):
            output_path = output_path.replace(".md", ".html")
        return output_path

    def build(self, files=None):
        # Load project data and globals
        data = {}

        # Get list of all files in project
        if files is None:
            files = self._scan()
        
        # Sort files into markdown and other
        md_files = [file for file in files if ".md" in file]
        other_files = [file for file in files if not ".md" in file]

        # Copy other files to output directory
        for file in other_files:
            output_path = self._get_output_path(file)
            if not os.path.exists(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))
            shutil.copyfile(file, output_path)

        # Process markdown files
        for md_file in md_files:
            content, metadata = Page.parse(md_file)
            render = Page.render(self.input_dir, content, metadata, data={})
            Page.save(render, self._get_output_path(md_file))

    # Check for modified files and only rebuild those
    def autobuild(self, kill_switch, server=None):
        last_modified = {}
        while not kill_switch.is_set():
            files = self._scan(include_templates=True)
            modified_files = []
            for file in files:
                if file not in last_modified.keys():
                    # File added since last scan
                    modified_files.append(file)
                    last_modified[file] = os.stat(file)[8]
                elif last_modified[file] < os.stat(file)[8]:
                    # File modified since last scan
                    modified_files.append(file)
                    last_modified[file] = os.stat(file)[8]

            # Look for changed templates
            build_files = []
            for file in modified_files:
                if file.endswith(".html"):

                    # Find all md files that use the changed template
                    md_files = [f for f in files if ".md" in f]
                    for md_file in md_files:
                        content, metadata = Page.parse(md_file)

                        if metadata.get("template", None) == os.path.basename(file):
                            build_files.append(md_file)
                else:
                    build_files.append(file)

            if len(build_files) > 0:
                print('')
                print("{} file(s) modified, rebuilding...".format(len(build_files)))
                self.build(files=build_files)

                # Notify autorefresh server
                if server:
                    server.notify()
            time.sleep(1)
        print("Shutting down autobuild process...")
        sys.exit(0)


class Page:
    
    @staticmethod
    def save(page, filepath):
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        with open(filepath, 'w', encoding="utf-8") as file:
            file.write(page) 

    @staticmethod
    def render(project_dir, page_content, metadata, data):
        # 'codehilite' for code highlighting
        # 'fenced_code' for code block definitions
        # 'toc' for table of contents
        # 'extra' for markdown inside html blocks
        md = markdown.Markdown(extensions=[AsideExtension(), 'fenced_code', TocExtension(baselevel=1), 'extra', 'wikilinks'])
        page_content = md.convert(page_content)
        template_path = os.path.join(project_dir, ".templates", metadata.get("template", ""))
        if not os.path.exists(template_path) or not os.path.isfile(template_path):
            template_path = os.path.join(SCRIPT_DIR, "templates", "default.html")

        with open(template_path, encoding="utf-8") as f:
            template = Template(f.read())

        return template.render(content=page_content,
                                toc=md.toc, 
                                 metadata=metadata,
                                 data=data)

    @staticmethod
    def parse(file):
        return FrontMatterParser.load_file(file)