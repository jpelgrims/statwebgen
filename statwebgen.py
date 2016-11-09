import os, os.path
import shutil
import glob
import markdown
import datetime
# 'Invisible' dependency on Pygments for markdown highlighting

def delete_file(filename):
    try:
        os.remove(filename)
    except:
        pass

INPUT_DIR = r'c:\users\jelle\desktop\website'
OUTPUT_DIR = r'c:\users\jelle\documents\github\jpelgrims'
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))

print("Converting Markdown files found in \'{}\' into static website at \'{}\'".format(INPUT_DIR, OUTPUT_DIR))

files = []
pattern   = "*"

# Get list of all files in input directory and subdirectorie
for dir,_,_ in os.walk(INPUT_DIR):
    files.extend(glob.glob(os.path.join(dir,pattern)))

# Sort files into markdown and other
md_files = [file for file in files if ".md" in file and os.path.isfile(file)]
other_files = [file for file in files if not ".md" in file and not ".html" in file and os.path.isfile(file)]

# Move other files to output directory
for file in other_files:
    copyfile = os.path.dirname(OUTPUT_DIR + file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.basename(file)
    try:
        os.makedirs(os.path.dirname(copyfile))
    except:
        pass
    shutil.copyfile(file, copyfile)

# Create index page (with post teasers) and blog page (with list of posts)
delete_file(INPUT_DIR + '\\' + 'index.md')
delete_file(INPUT_DIR + '\\' + 'blog.md')

topics = {}
teasers = {}

for md_file in [file for file in md_files if "posts" in file]:

    with open(md_file, 'r') as file:
        content = file.readlines()

    try:
        title = content[0][2:]
        topic = content[2][7:].replace("</small>", "")
        creation_data = content[4]
        created_date = datetime.datetime.strptime(creation_data[14:25].replace(" ", ""), "%d/%m/%Y")
        first_paragraph = content[6]
        post_link = "[Read more](/posts/" + title.replace(" ", "_") + ".html)"
        md_teaser = "\n".join(["## " + title, creation_data, first_paragraph, post_link, "\n"])

        if topic not in topics.keys():
            topics[topic] = [title]
        else:
            topics[topic].append(title)

        if created_date not in teasers.keys():
            teasers[created_date] = [md_teaser]
        else:
            teasers[created_date].append(md_teaser)
    
    except Exception as e:
        # Faulty post
        print(e)

with open(INPUT_DIR + '\\' + 'blog.md', 'a') as blog:
    for topic, titles in topics.items():
        blog.write("## " + topic + "\n")
        for title in titles:
            post_link = ("[{}](/posts/" + title.replace(" ", "_") + ".html)").format(title)
            blog.write("   * " + post_link + "\n")
        blog.write("\n")

with open(INPUT_DIR + '\\' + 'index.md', 'a') as index:
    for created_date, teasers in sorted(teasers.items(), key=lambda t: t[0], reverse=True):
        for teaser in teasers:
            index.write(teaser)

# Load page template
with open((INPUT_DIR + '\\' + 'template.html'), 'r') as file:
    template = file.read()

# Loop over all content files
for md_file in md_files:
    with open(md_file, 'r') as file:
        content = file.readlines()
    
    # Convert markdown to html
    post = markdown.markdown("".join(content), extensions=['codehilite', 'fenced_code', 'toc'])
    
    # Use page template
    page = template.replace('<%post%>', post)

    # Save to output directory
    outputfile = os.path.dirname(OUTPUT_DIR + md_file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.splitext(os.path.basename(md_file))[0] + '.html'
    try:
        os.makedirs(os.path.dirname(outputfile))
    except:
        pass
    with open(outputfile, 'w') as file:
        file.write(page)

print('Succesfully created static site @', OUTPUT_DIR)

