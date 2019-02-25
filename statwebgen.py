import os
import os.path
import sys
import shutil
from distutils.dir_util import copy_tree
import glob
import time
import threading
import http.server
import socketserver
import webbrowser

import json
import markdown
import argparse
import signal

from jinja2 import Template

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).lower()

REFRESH_SCRIPT = ""
with open(os.path.join(SCRIPT_DIR, 'live_refresh.js'), 'r') as j:
    REFRESH_SCRIPT = '<script>' + j.read() + '</script>'

# Parser for page front matter
#    * Simple key/value pairings
#    * Comma-separated lists between brackets
#    * Keys are case insensitive

class FMML():

    @staticmethod
    def load(filepath):
        with open(filepath, 'r', encoding="utf-8") as f:
            return FMML.parse_text(f.read())

    @staticmethod
    def parse_text(raw_text):
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
            

class LiveRefreshHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        # Endpoint for checking if live refresh is required
        if self.path == '/_refresh':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            message = json.dumps({"refresh": self.server.refresh_required}).encode("utf-8")
            self.wfile.write(message)

            self.server.refresh_required = False

    def end_headers(self):
        # Allow CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    @staticmethod
    def signal_handler(signal, frame):
        print('Shutting down web server...')
        sys.exit(0)


class LiveRefreshServer(socketserver.TCPServer):

    def __init__(self, server_address):
        self.refresh_required = False
        super().__init__(server_address, LiveRefreshHandler)

    def serve_forever(self):
        super().serve_forever()
    
    def notify(self):
        self.refresh_required = True

class StaticWebsiteHandler(http.server.SimpleHTTPRequestHandler):

    def modify_header(self, keyword, value):
        for i in range(len(self._headers_buffer)):
            item = self._headers_buffer[i]
            if keyword.encode('utf-8') in item:
                 del self._headers_buffer[i]
                 self.send_header(keyword, value)
                 break

    def end_headers(self):
        path = self.translate_path(self.path)

        if self.guess_type(path) == "text/html":

            f = open(path, 'rb')
            fs = os.fstat(f.fileno())

            # Set correct Content-length (file length + length of refresh script)
            self.modify_header("Content-Length", str(fs[6] + len(REFRESH_SCRIPT)))
        super().end_headers()


    def do_GET(self):
        f = self.send_head()
        if f:
            try:
                if f.name.endswith(".html"):
                    lines = f.readlines()

                    for line in lines:
                        # Insert live-refresh script in head
                        if b"</head>" in line:
                            self.wfile.write(REFRESH_SCRIPT.encode('utf-8'))

                        self.wfile.write(line)

                        

                else:
                    self.copyfile(f, self.wfile)

            finally:
                f.close()

    def translate_path(self,path):
        root = os.getcwd()
        if path[-1] != "/" and not "." in path[-5:]:
            return root + path + ".html"
        else:
            return root + path

    @staticmethod
    def signal_handler(signal, frame):
        print('Shutting down web server...')
        sys.exit(0)

# Set handler function for SIGINT signal (i.e. Control-C)
signal.signal(signal.SIGINT, StaticWebsiteHandler.signal_handler)
signal.signal(signal.SIGINT, LiveRefreshHandler.signal_handler)


class Website:

    def __init__(self, input_dir, output_dir=None):
        self.input_dir = input_dir.lower()

        if not output_dir:
            self.output_dir = os.path.join(self.input_dir, ".build")
        else:
            self.output_dir = output_dir.lower()
        
        self.exclude_dir = [f.name for f in os.scandir(self.input_dir) if f.is_dir() and f.name.startswith(".")]

    def serve(self, port=8080, browser=False, directory=None):
        if not directory:
            directory = self.output_dir

        os.chdir(directory) 
        while True:
            try:
                server = socketserver.TCPServer(("", port), StaticWebsiteHandler)
                break
            except:
                print("Port {} already in use. Using port {} instead...".format(port, port+1))
                port += 1
        
        if browser:
            webbrowser.open("http://localhost:{}/".format(port), new=0)

        print("Serving at port", port)
        server.serve_forever()

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
            output_path = output_path.rstrip(".md") + '.html'
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
    def autobuild(self, server):
        last_modified = {}
        while True:
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
                    print(os.path.basename(file))
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
                server.notify()
            time.sleep(1)


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
        md = markdown.Markdown(extensions=['fenced_code', 'toc', 'extra'])
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
        raw_page = None
        with open(file, "r", encoding="utf-8") as f:
            raw_page = f.read()

        # Extract metadata
        index = raw_page.find("---")
        raw_metadata = raw_page[0:index].replace("---\n", "")
        metadata = FMML.parse_text(raw_metadata)

        # Extract page content
        content = raw_page[index:].strip("\n").strip("---")

        return content, metadata


def process_arguments(arguments):
    config_file = os.path.join(SCRIPT_DIR, 'config.ini')
    config = FMML.load(config_file)

    # Use the path from the config file if a project is specified in the arguments
    project_path = arguments.path
    if arguments.project:
        if arguments.project in config.keys():
            project_path = config[arguments.project]
        else:
            if not arguments.create:
                print("The specified project does not exist.")
                exit(0)

    if arguments.create and arguments.project:

        config[arguments.project] = arguments.path

        if arguments.skeleton:
            try:
                copy_tree(os.path.join(SCRIPT_DIR, "skeletons", arguments.skeleton), arguments.path)
            except:
                print("Something went wrong while creating a new project.")
        
        print("Project '{}' was successfully created in {}.".format(arguments.project, arguments.path))
        FMML.save(config, config_file)
    
    if arguments.build or arguments.watch:
        website = Website(project_path)
        if arguments.build:
            website.build()
            print("Website build complete.")
        elif arguments.watch:
            # Live refresh endpoint
            server = LiveRefreshServer(("", 8001))
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()

            thread = threading.Thread(target=website.autobuild, args=(server,))
            thread.daemon = True
            thread.start()
        
    if arguments.serve:
        website = Website(project_path)
        website.serve(port=8000, browser=arguments.open)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Statwebgen - Static website generator')
    parser.add_argument('-v', '--version', action='version', version='statwebgen 0.1')
    parser.add_argument('-c', '--create', action='store_true', help='Create a project')
    parser.add_argument('--skeleton', help='Choose a project skeleton')
    parser.add_argument('--project', help='Choose a project')
    parser.add_argument('-b', '--build', action='store_true', help='Build the project')
    parser.add_argument('-w', '--watch', action='store_true', help='Automatically rebuild the project on changes')
    parser.add_argument('-s', '--serve', action='store_true', help='Serve the project locally')
    parser.add_argument('-o', '--open', action='store_true', help='Open the project in the default browser')
    parser.add_argument('-p', '--publish', action='store_true', help='Publish the project')
    parser.add_argument('path', nargs='?', action='store', type=str, default=os.getcwd(), help='Project file path, defaults to current working directory')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    process_arguments(args)