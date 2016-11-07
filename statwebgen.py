import os, os.path
import shutil
import glob
import markdown
# 'Invisible' dependency on Pygments for markdown highlighting

INPUT_DIR = r'c:\users\jelle\desktop\website'
OUTPUT_DIR = r'c:\users\jelle\documents\github\jpelgrims'
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))

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

# Load page template
with open((INPUT_DIR + '\\' + 'template.html'), 'r') as file:
    template = file.read()

# Loop over all content files
for md_file in md_files:
    with open(md_file, 'r') as file:
        content = file.read()

    # Convert markdown to html
    post = markdown.markdown(content, extensions=['codehilite', 'fenced_code', 'toc'])
    
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

