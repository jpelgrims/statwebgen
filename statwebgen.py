import markdown
import datetime
import os

class Page:

    def __init__(self, template):
        self.template = template
        self.type = ""
        self.title = ""
        self.category = ""
        self.description = ""
        self.created = None
        self.updated = None
        self.javascript = []
        self.content = []
        self.teaser = ""

    def load(self, filepath=None, page=None):
        
        if filepath:
            self.filepath = filepath
            with open(self.filepath, 'r') as file:
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

        if self.type == 'page':
            self.content = "#" + self.title + "\n\n" + "".join(page[8:])
        elif self.type =='post':
            self.content = "#" + self.title + "\n\n**Table of contents**\n" + "\n[TOC]\n\n" +  "".join(page[8:])
            post_link = "[Read more...](/posts/" + self.title.lower().replace(" ", "_") + ".html)"
            self.teaser = "\n".join(["## " + self.title, 
                                    "<small>Created on " + self.created.strftime("%d/%m/%Y") + ", last updated on " + self.updated.strftime("%d/%m/%Y") + "</small>\n", 
                                    page[8], post_link, "\n"])

    def _to_html(self, template_file):
        with open(template_file, 'r') as file:
            template = file.read()

        html = markdown.markdown(self.content, extensions=['codehilite', 'fenced_code', 'toc', 'extra'])
        script_includes = "".join(["<script type='text/javascript' async src='/javascript/{}'></script>\n".format(script) for script in self.javascript if not 'mathjax.js' in script])
        
        #Check for mathjax because it needs a special include due to it being loaded from an external source
        for script in self.javascript:
            if 'mathjax.js' in script:
                script_includes += "<script type='text/javascript' async src='https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n"
                break

        html_page = template
        for tag, tag_content in {'<%scripts%>': script_includes, '<%post%>': html, '<%title%>': self.title, '<%description%>': self.description}.items():
            html_page = html_page.replace(tag, tag_content)
        
        return html_page

    def save(self, filepath):
        # Make sure directory exists, if not, create it
        try:
            os.makedirs(os.path.dirname(filepath))
        except:
            pass
        with open(filepath, 'w') as file:
            file.write(self._to_html(self.template))
