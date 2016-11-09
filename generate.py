import os, os.path
import shutil
import glob
import markdown
import datetime
# 'Invisible' dependency on Pygments for markdown highlighting

from statwebgen import Page


INPUT_DIR = r'c:\users\jelle\desktop\website'
OUTPUT_DIR = r'c:\users\jelle\documents\github\jpelgrims'
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
EXCLUDE_DIR = [r'c:\users\jelle\desktop\website\drafts']

print("Converting Markdown files found in \'{}\' into static website at \'{}\'".format(INPUT_DIR, OUTPUT_DIR))

files = []
pattern   = "*"

# Get list of all files in input directory and subdirectorie
for dir,_,_ in os.walk(INPUT_DIR):
    files.extend(glob.glob(os.path.join(dir,pattern)))

# Sort files into markdown and other
md_files = [file for file in files if ".md" in file and os.path.isfile(file) and not "drafts" in file]
other_files = [file for file in files if not ".md" in file and not ".html" in file and os.path.isfile(file) and not file in EXCLUDE_DIR]

# Copy other files to output directory
for file in other_files:
    copyfile = os.path.dirname(OUTPUT_DIR + file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.basename(file)
    try:
        os.makedirs(os.path.dirname(copyfile))
    except:
        pass
    shutil.copyfile(file, copyfile)

# Turn all markdown files into Page objects
template_file = INPUT_DIR + '\\' + 'template.html'
pages = []

for md_file in md_files:
    page_type = "page"
    if "posts" in md_file:
        page_type = "post"
    page = Page(template_file, page_type)
    page.load(filepath=md_file)
    pages.append(page)
    outputfile = os.path.dirname(OUTPUT_DIR + md_file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.splitext(os.path.basename(md_file))[0] + '.html'
    page.save(outputfile)

# Create index page (with post teasers) and blog page (with list of posts)
posts = [page for page in pages if page.type == 'post']
topics = {}
teasers = {}

for post in posts:
    if post.topic not in topics.keys():
         topics[post.topic] = [post.title]
    else:
        topics[post.topic].append(post.title)

    if post.created not in teasers.keys():
        teasers[post.created] = [post.teaser]
    else:
        teasers[post.created].append(post.teaser)

md_blog = []
for topic, titles in topics.items():
    md_blog.append("## " + topic + "\n")
    for title in titles:
        post_link = ("[{}](/posts/" + title.lower().replace(" ", "_") + ".html)").format(title)
        md_blog.append("   * " + post_link + "\n")
    md_blog.append("\n")
md_blog = "".join(md_blog)
    
blog = Page(template_file, 'page')
blog.load(page=md_blog)
blog.save(OUTPUT_DIR + '\\' + 'blog.html')

md_index = []
for created_date, teasers in sorted(teasers.items(), key=lambda t: t[0], reverse=True):
    for teaser in teasers:
        md_index.append(teaser)
md_index = "".join(md_index)

index = Page(template_file, 'page')
index.load(page=md_blog)
index.save(OUTPUT_DIR + '\\' + 'index.html')

print('Succesfully created static site @', OUTPUT_DIR)

