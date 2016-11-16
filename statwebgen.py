import os, os.path, sys
import shutil
import glob

import string
import datetime
import markdown
import json
import re

import http.server
import socketserver
from urllib.parse import urlparse

# 'Invisible' dependency on Pygments for markdown highlighting


class StaticWebsiteHandler(http.server.SimpleHTTPRequestHandler):

    def translate_path(self,path):
        root = os.getcwd()
        if path[-1] != "/" and not "." in path[-4:]:
            return root + path + ".html"
        else:
            return root + path


class Website:

    def __init__(self, config_file):
        print('Loading configuration file...', end=" ")
        with open(config_file, 'r') as file:
            settings = json.loads(file.read())

        self.name = settings['PROJECT_NAME']
        self.input_dir = settings['INPUT_DIR']
        self.output_dir = settings['OUTPUT_DIR']
        self.exclude_dir = settings['EXCLUDE_DIR']

        print("done.\n")

    def serve(self, port=8000):
        os.chdir("c:\\users\\jelle\\documents\\github\\jpelgrims")

        while True:
            try:
                httpd = socketserver.TCPServer(("", port), StaticWebsiteHandler)
                break
            except:
                print("Port {} already in use. Using port {} instead...".format(port, port+1))
                port += 1

        print("Serving at port", port)
        os.startfile("http://localhost:{}/".format(port))
        httpd.serve_forever()
        
    def publish(self, message):
        os.chdir(self.output_dir)
        os.system('git add --all')
        os.system('git commit -m "{}"'.format(message))
        os.system('git push')

    def build(self):
        files = []
        pattern   = "*"

        # Get list of all files in input directory and subdirectory
        for dir,_,_ in os.walk(self.input_dir):
            files.extend(glob.glob(os.path.join(dir,pattern)))

        print("Project: '{}', consisting of {} files".format(self.name, len(files)))
        print("Input directory: {}".format(self.input_dir))
        print("Output directory: {}".format(self.output_dir))
        print("")

        # Sort files into markdown and other
        md_files = [file for file in files if ".md" in file and os.path.isfile(file) and not "drafts" in file]
        other_files = [file for file in files if not ".md" in file and not ".html" in file and os.path.isfile(file) and not file in self.exclude_dir]

        # Copy other files to output directory
        print('Copying {} non-markdown files to output directory...'.format(len(other_files)), end=" ")
        for file in other_files:
            copyfile = os.path.dirname(self.output_dir + file.lower().replace(self.input_dir,'')) + '\\' + os.path.basename(file)
            try:
                os.makedirs(os.path.dirname(copyfile))
            except:
                pass
            shutil.copyfile(file, copyfile)
        print("done.")

        # Turn all markdown files into Page objects
        pages = []

        print("Processing markdown pages...")

        for md_file in md_files:
            # layout should depend on page type (e.g. layout = page_type + '\\' + "_layout.html")
            page = Page(self.input_dir + '\\layout.html', filepath=md_file)
            pages.append(page)

        #Need to collect website data (post metadata, ...) first for template code that could use it
        data = {page.title: page.metadata for page in pages}

        # Save all files as html
        for page in pages:
            print("   * {}".format(os.path.basename(page.input_file)))
            output_file = os.path.dirname(self.output_dir + page.input_file.lower().replace(self.input_dir,'')) + '\\' + os.path.splitext(os.path.basename(page.input_file))[0] + '.html'
            page.save(output_file, data)

        print('')
        print('Static site creation succesfull!')

class Page:

    def __init__(self, layout, filepath=None):
        self.layout = layout
        if filepath:
            self.load(filepath=filepath)

    def load(self, filepath=None, page=None):

        if filepath:
            self.input_file = filepath
            with open(self.input_file, 'r') as file:
                page = file.readlines()

        metadata = {}
        for i in range(7):
            temp = page[i].split(":")
            tag, data = temp[0].lower(), temp[1].strip()
            metadata[tag] = data

        self.type = metadata['type']
        self.title = metadata['title']
        self.description = metadata['description']
        self.category = metadata['category']
        self.created = datetime.datetime.strptime(metadata['created'], "%d/%m/%Y")
        self.updated = datetime.datetime.strptime(metadata['updated'], "%d/%m/%Y")
        self.javascript = [item.strip() for item in metadata['javascript'].split(",")]
        self.raw_content = "".join(page[8:])
        self.metadata = metadata
        self.metadata['first_paragraph'] = page[10]

    def _substitute_templates(self, raw_content, data):
        # Check for templates in content, use eval on template code, grab eval output and replace templates with output
        scripts = re.findall('(\{\{[\s\S]+\}\})',raw_content)
        for script in scripts:
            namespace = {'data':data}
            exec(script[2:-2], namespace)
            raw_content = raw_content.replace(script, namespace['output'])
        return raw_content

    def _to_html(self, data):
        with open(self.layout, 'r') as file:
            layout = file.read()

        sidebar = ''

        #Codehilite for code highlighting, 'fenced_code' for ..., 'toc' for table of contents, 'extra' for markdown inside html blocks, 'meta' for metadata
        md = markdown.Markdown(extensions=['codehilite', 'fenced_code', 'toc', 'extra', 'meta'])
        html = md.convert(self._substitute_templates(self.raw_content, data))
        script_includes = "".join(["<script type='text/javascript' async src='/javascript/{}'></script>\n".format(script) for script in self.javascript if not 'mathjax.js' in script])
        
        #Check for mathjax because it needs a special include due to it being loaded from an external source
        for script in self.javascript:
            if 'mathjax.js' in script:
                script_includes += "<script type='text/javascript' async src='https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n"
                break

        html_page = layout
        substitutions = {'<%scripts%>': script_includes,
                         '<%post%>': html, 
                         '<%title%>': self.title, 
                         '<%description%>': self.description, 
                         '<%sidebar%>': sidebar}

        for tag, tag_content in substitutions.items():
            html_page = html_page.replace(tag, tag_content)
        
        return html_page

    def save(self, filepath, data):
        # Make sure directory exists, if not, create it
        try:
            os.makedirs(os.path.dirname(filepath))
        except:
            pass
        with open(filepath, 'w') as file:
            file.write(self._to_html(data))

def main(argv):
    print('StatWebGen 0.1 ready.')

    WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
    config_file = WORKING_DIR + '\config.json'
    website = Website(config_file)

    if argv[0] == 'serve':
        website.serve(port=8000)
    elif argv[0] == 'build':
        website.build()
    elif argv[0] == 'publish':
        website.publish(argv[1])
       

if __name__ == "__main__":
   main(sys.argv[1:])