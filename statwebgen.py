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

import json
import markdown



WORKING_DIR = os.path.dirname(os.path.realpath(__file__))

class StaticWebsiteHandler(http.server.SimpleHTTPRequestHandler):

    def translate_path(self,path):
        root = os.getcwd()
        if path[-1] != "/" and not "." in path[-5:]:
            return root + path + ".html"
        else:
            return root + path


class Website:

    def __init__(self, input_dir, output_dir=None):
        self.input_dir = input_dir.lower()

        if not output_dir:
            self.output_dir = os.path.join(self.input_dir, ".build")
        else:
            self.output_dir = output_dir.lower()
        
        self.exclude_dir = ["\\old", "\\drafts", "\\.build", "\\templates"]

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
            os.startfile("http://localhost:{}/".format(port))

        print("Serving at port", port)
        server.serve_forever()
        
    # only if github Website
    # maybe add sftp publishing?
    def publish(self, message):
        os.chdir(self.output_dir)
        os.system('git add --all')
        os.system('git commit -m "{}"'.format(message))
        os.system('git push')


    def _scan(self):
        # Returns a list of all files in the project directory and all subdirectories (except exluded files & directories)
        files = []
        pattern   = "*"

        for dir,_,_ in os.walk(self.input_dir):
            files.extend(glob.glob(os.path.join(dir,pattern)))
        
        files = [file for file in files if not any(dir in file for dir in self.exclude_dir) ]

        return files

    def build(self, files=None):
        if files is None:
            files = self._scan()

        # Sort files into markdown and other
        md_files = [file for file in files if ".md" in file and os.path.isfile(file)]
        other_files = [file for file in files if not ".md" in file in file and os.path.isfile(file)]

        # Copy other files to output directory
        for file in other_files:
            copyfile = os.path.dirname(self.output_dir + file.lower().replace(self.input_dir,'')) + '\\' + os.path.basename(file)
            try:
                os.makedirs(os.path.dirname(copyfile))
            except:
                pass
            shutil.copyfile(file, copyfile)

        # Turn all markdown files into Page objects
        pages = []

        for md_file in md_files:
            try:
                page = Page(filepath=md_file, input_dir=self.input_dir)
                pages.append(page)
            except Exception as error:
                print("   * An error occured while trying to parse {} meta-data.".format(os.path.basename(md_file)))
                print(error)

        # Save all files as html
        for page in pages:
            output_file = os.path.dirname(self.output_dir + page.input_file.lower().replace(self.input_dir,'')) + '\\' + os.path.splitext(os.path.basename(page.input_file))[0] + '.html'
            page.save(output_file)

    # Check for modified files and only rebuild those
    # Currently works with metadata, but will maybe add hashing in future
    def autobuild(self):
        last_modified = {}
        while True:
            files = self._scan()
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
            if len(modified_files) > 0:
                print('')
                print("{} file(s) modified, rebuilding...".format(len(modified_files)))
                self.build(files=modified_files)
            time.sleep(1)

class Page:

    def __init__(self, filepath=None, input_dir=None):
        if filepath:
            self.load(filepath=filepath)

        self.input_dir = None
        if input_dir:
            self.input_dir = input_dir

    def load(self, filepath=None, page=None):

        if filepath:
            self.input_file = filepath
            with open(self.input_file, 'r') as file:
                page = file.readlines()

        metadata = {}
        
        start_index = 0
        if "---\n" in page: # Check to see if page actually includes meta-data
            for i in range(len(page)-1):
                if "---" in page[i]:
                    start_index = i+1
                    break
                temp = page[i].split(":")
                tag, data = temp[0].lower(), temp[1].strip()
                if "," in data:
                    data = data.split(",")
                    data = [element.strip() for element in data]
                metadata[tag] = data
        
        self.filename = os.path.basename(os.path.splitext(self.input_file)[0])

        self.raw_content = "".join(page[start_index:])
        self.metadata = metadata

    def _to_html(self):
        template = self.metadata.get("template")
        if template:
            template = os.path.join(self.input_dir, 'templates' + '\\' + template)
        else:
            # No template set, use default template
            template = WORKING_DIR + '\\templates\default.html'

        with open(template, 'r') as file:
            layout = file.read()

        # 'codehilite' for code highlighting, 
        # 'fenced_code' for code block definitions
        # 'toc' for table of contents
        # 'extra' for markdown inside html blocks

        md = markdown.Markdown(extensions=['fenced_code', 'toc', 'extra'])
        html = md.convert(self.raw_content)

        script_includes = ""
        if self.metadata.get('javascript') is not None:
            scripts = self.metadata.get('javascript')
            if isinstance(scripts, str):
                scripts = [scripts]
            script_includes = "".join(["<script type='text/javascript' async src='./javascript/{}'></script>\n".format(script) for script in scripts if not 'mathjax.js' in script])
        
            # Check for mathjax/aes because they need a special include due to it being loaded from an external source
            if 'mathjax.js' in self.metadata.get('javascript'):
                script_includes += "<script type='text/javascript' async src='https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n"

        css_includes = ""
        if self.metadata.get('stylesheets') is not None:
            sheets = self.metadata.get('stylesheets')
            #print(sheets)
            if isinstance(sheets, str):
                sheets = [sheets]
            css_includes = "".join(["<link rel='stylesheet' type='text/css' href='/css/{}' />\n".format(sheet) for sheet in sheets])

        html_page = layout

        # replace all html includes (for footers and navbars and stuff)

        html_files = []
        pattern   = "*.html"

        # HTML substitutions

        # Get list of all html files in templates dir
        for dir,_,_ in os.walk('templates' + '\\'):
            html_files.extend(glob.glob(os.path.join(dir,pattern)))
        
        html_substitutions = {}
        for html_file in html_files:
            with open(html_file) as file:
                html_content = file.read()
            html_substitutions["<!" + os.path.basename(html_file) + ">"] = html_content

        for tag, tag_content in html_substitutions.items():
            html_page = html_page.replace(tag, tag_content)

        # Meta-data substitutions

        substitutions = {'<!javascript>': script_includes,
                         '<!stylesheets>': css_includes,
                         '<!page-content>': html}

        for tag, tag_content in substitutions.items():
            html_page = html_page.replace(tag, tag_content)
        
        for tag, value in self.metadata.items():
            html_page = html_page.replace("$"+tag, str(value))
        
        return html_page

    def save(self, filepath):
        # Make sure directory exists, if not, create it
        try:
            os.makedirs(os.path.dirname(filepath))
        except:
            pass
        with open(filepath, 'w') as file:
            file.write(self._to_html())

def get_project_directory(path_or_name):

    config = {}
    with open(os.path.join(WORKING_DIR, 'config.json'), 'r') as f: 
        contents = f.read()
        config = json.loads(contents)

    if os.path.exists(path_or_name):
        return path_or_name
    elif path_or_name in config.keys():
        return config[path_or_name]
    else:
        return None

def main(argv):

    config = {}
    with open(os.path.join(WORKING_DIR, 'config.json'), 'r') as f: 
        contents = f.read()
        config = json.loads(contents)

    if argv[0] == 'create':

        if len(argv) >= 3:
            skeleton = "default"
            name = argv[-2]
            path = argv[-1]

            if "--skeleton" in argv:
                skeleton = argv[2]
            
            try:
                copy_tree(os.path.join(WORKING_DIR, "skeletons", skeleton), path)
            except:
                print("Something went wrong while creating a new project.")

            config[name] = path
            print("Project {} was successfully created.".format(name))

    elif argv[0] == 'serve':
        open_browser = False

        project_dir = os.path.join(get_project_directory(argv[-1]), ".build")
        website = Website(project_dir)

        if len(argv) >= 3:

            small_browser_flag = len(argv[1]) <= 3 and argv[1].startswith("-") and "b" in argv[1]
            large_browser_flag = "--browser" in argv

            if small_browser_flag or large_browser_flag:
                open_browser = True

            small_watch_flag = len(argv[1]) <= 3 and argv[1].startswith("-") and "w" in argv[1]
            large_watch_flag = "--watch" in argv

            if small_watch_flag or large_watch_flag:
                thread = threading.Thread(target=website.autobuild)
                thread.daemon = True
                thread.start()

        website.serve(port=8000, browser=open_browser, directory=project_dir)

    elif argv[0] == 'build':

        if len(argv) >= 2:
            output_dir = None

            if argv[1] in ["-a", "--auto"]:
                if len(argv) == 3:
                    project_dir = get_project_directory(argv[-1])
                elif len(argv) == 4:
                    project_dir = get_project_directory(argv[-2])
                    output_dir = argv[-1]
                website = Website(project_dir, output_dir=output_dir)
                website.autobuild()
            else:
                if len(argv) == 2:
                    project_dir = get_project_directory(argv[-1])
                elif len(argv) == 3:
                    project_dir = get_project_directory(argv[-2])
                    output_dir = argv[-1]
                website = Website(project_dir, output_dir=output_dir)
                website.build()

            print("Website build complete.")
        
    elif argv[0] == 'publish':
        pass  
    
    with open(os.path.join(WORKING_DIR, 'config.json'), 'w') as f: 
        f.write(json.dumps(config))

if __name__ == "__main__":
   main(sys.argv[1:])