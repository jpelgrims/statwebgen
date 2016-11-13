import os, os.path
import shutil
import glob
import json
import markdown
import datetime
# 'Invisible' dependency on Pygments for markdown highlighting

from statwebgen import Page

print('StatWebGen 0.1 ready.')
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))

print('Loading configuration file...', end=" ")
with open(WORKING_DIR + '\config.json', 'r') as file:
    settings = json.loads(file.read())

PROJECT_NAME = settings['PROJECT_NAME']
INPUT_DIR = settings['INPUT_DIR']
OUTPUT_DIR = settings['OUTPUT_DIR']
EXCLUDE_DIR = settings['EXCLUDE_DIR']

print("done.")
print("")

files = []
pattern   = "*"

# Get list of all files in input directory and subdirectorie
for dir,_,_ in os.walk(INPUT_DIR):
    files.extend(glob.glob(os.path.join(dir,pattern)))

print("Project: '{}', consisting of {} files".format(PROJECT_NAME, len(files)))
print("Input directory: {}".format(INPUT_DIR))
print("Output directory: {}".format(OUTPUT_DIR))
print("")

# Sort files into markdown and other
md_files = [file for file in files if ".md" in file and os.path.isfile(file) and not "drafts" in file]
other_files = [file for file in files if not ".md" in file and not ".html" in file and os.path.isfile(file) and not file in EXCLUDE_DIR]

# Copy other files to output directory
print('Copying {} non-markdown files to output directory...'.format(len(other_files)), end=" ")
for file in other_files:
    copyfile = os.path.dirname(OUTPUT_DIR + file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.basename(file)
    try:
        os.makedirs(os.path.dirname(copyfile))
    except:
        pass
    shutil.copyfile(file, copyfile)
print("done.")

# Turn all markdown files into Page objects
template_file = INPUT_DIR + '\\' + 'template.html'
pages = []

print("Processing markdown pages...")

for md_file in md_files:
    page = Page(template_file)
    page.load(filepath=md_file)
    print("   * {}".format(os.path.basename(page.filepath)))
    pages.append(page)
    outputfile = os.path.dirname(OUTPUT_DIR + md_file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.splitext(os.path.basename(md_file))[0] + '.html'
    page.save(outputfile)

# Create index page (with post teasers) and blog page (with list of posts)
posts = [page for page in pages if page.type == 'post']
categories = {}
teasers = {}

for post in posts:
    if post.category not in categories.keys():
         categories[post.category] = [post.title]
    else:
        categories[post.category].append(post.title)

    if post.created not in teasers.keys():
        teasers[post.created] = [post.teaser]
    else:
        teasers[post.created].append(post.teaser)

print("Building blog page...", end=" ")
blog = Page(template_file)
blog.title = "Blog"
blog.description = "List of all published posts"

for category, titles in categories.items():
    blog.content.append("## " + category + "\n")
    for title in titles:
        post_link = ("[{}](/posts/" + title.lower().replace(" ", "_") + ".html)").format(title)
        blog.content.append("   * " + post_link + "\n")
    blog.content.append("\n")

blog.content = "".join(blog.content)
blog.save(OUTPUT_DIR + '\\' + 'blog.html')
print("done.")

print("Building index page...", end=" ")
index = Page(template_file)
index.title = "Index"
index.description = "Homepage"

for created_date, teasers in sorted(teasers.items(), key=lambda t: t[0], reverse=True):
    for teaser in teasers:
        index.content.append(teaser)

index.content = "".join(index.content)
index.save(OUTPUT_DIR + '\\' + 'index.html')
print('done.')
print('')
print('Static site creation succesfull!')

