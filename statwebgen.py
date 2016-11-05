import os, os.path
import shutil
import glob

INPUT_DIR = r'c:\users\jelle\desktop\website'
OUTPUT_DIR = r'c:\users\jelle\documents\github\jpelgrims'
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
EXCLUDE_DIRS = [WORKING_DIR.lower(),
                r'c:\users\jelle\desktop\website\.idea',
                r'c:\users\jelle\desktop\website\.idea\copyright']

files = []
pattern   = "*"

variables = {
    '<%head%>': 'head.html',
    '<%header%>': 'header.html',
    '<%footer%>': 'footer.html'}

for dir,_,_ in os.walk(INPUT_DIR):
    # Avoid adding statwebgen files when statwebgen in project directory
    if dir.lower() in EXCLUDE_DIRS:
        continue
    files.extend(glob.glob(os.path.join(dir,pattern)))

# Sort files into html and other
html_files = [file for file in files if ".html" in file and os.path.isfile(file)]
other_files = [file for file in files if not ".html" in file and os.path.isfile(file)]

# Move other files to output directory
for file in other_files:
    copyfile = os.path.dirname(OUTPUT_DIR + file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.basename(file)
    try:
        os.makedirs(os.path.dirname(copyfile))
    except:
        pass
    shutil.copyfile(file, copyfile)

# Change variables with corresponding html and write to output directory
for html_file in html_files:
    with open(html_file, 'r') as file:
        content = file.read()
    for variable, filepath in variables.items():
        with open((WORKING_DIR + '\\' + filepath), 'r') as file:
            html = file.read()
        content = content.replace(variable, html)

    outputfile = os.path.dirname(OUTPUT_DIR + html_file.lower().replace(INPUT_DIR,'')) + '\\' + os.path.basename(html_file)
    try:
        os.makedirs(os.path.dirname(outputfile))
    except:
        pass
    with open(outputfile, 'w') as file:
        file.write(content)

print('Succesfully created static site @', OUTPUT_DIR)

