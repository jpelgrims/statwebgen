import markdown
import datetime

class Page:

    def __init__(self, template, page_type):
        self.template = template
        self.type = page_type
        self.title = None
        self.topic = None
        self.description = None
        self.created = None
        self.updated = None
        self.content = None
        self.teaser = None

    def load(self, filepath=None, page=None):
        if filepath:
            self.filepath = filepath
            with open(self.filepath, 'r') as file:
                page = file.readlines()

        if self.type in ['page', 'post']:
            self.title = page[0][2:]
            self.content = "\n".join(page[0:])
        if self.type == 'post':
            self.topic = page[2][7:].replace("</small>", "")
            creation_data = page[4]
            self.created = datetime.datetime.strptime(creation_data[14:25].replace(" ", ""), "%d/%m/%Y")
            self.content = "#" + self.title + "\n\n**Table of contents**\n" + "\n[TOC]\n\n" +  "".join(page[10:])
            post_link = "[Read more...](/posts/" + self.title.lower().replace(" ", "_") + ".html)"
            self.teaser = "\n".join(["## " + self.title, creation_data, page[10], post_link, "\n"])

    def _to_html(self, template_file):
        with open(template_file, 'r') as file:
            template = file.read()

        html = markdown.markdown(self.content, extensions=['codehilite', 'fenced_code', 'toc'])
        html_page = template.replace('<%post%>', html)
        
        return html_page

    def save(self, filepath):
        # Make sure directory exists, if not, create it
        try:
            os.makedirs(os.path.dirname(outputfile))
        except:
            pass
        with open(filepath, 'w') as file:
            file.write(self._to_html(self.template))
