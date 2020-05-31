# statwebgen
A simple static website generator. I use it for my persal website, found [here](http://www.jellepelgrims.com).

## Features

*   Create static websites from markdown files
*   Jinja2 templating
*   Automatic site rebuilding (no need to rebuild after every change)
*   Live refresh webserver for testing included
*   Automated publishing to github (with git)

### Usage

```
$ python3 statwebgen.py -h

usage: statwebgen.py [-h] [-v] {create,build,watch,serve,clean} ...

Build static websites.

positional arguments:
  {create,build,watch,serve,clean}
                        All available subcommands
    create              Create a new static website
    build               Build a static website
    watch               Rebuild a static website on changes
    serve               Serve a static website locally and rebuild on changes
    clean               Empty the build folder of a project

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
```

#### Create command

Creates a new project from a template (if no template is given, uses the default template).

```
$ python3 statwebgen.py create -h

usage: statwebgen.py create [-h] [-n NAME] [-p PATH] [-s SKELETON]

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Project name
  -p PATH, ---path PATH
                        Project path
  -s SKELETON, --skeleton SKELETON
                        Project skeleton to start with
```

#### Build command

Builds the project.

```
$ python3 statwebgen.py build -h

usage: statwebgen.py build [-h] [-i INPUT_FOLDER] [-o OUTPUT_FOLDER]
                           [-p PROJECT] [-t]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FOLDER, --in INPUT_FOLDER
                        Input folder
  -o OUTPUT_FOLDER, --out OUTPUT_FOLDER
                        Output folder
  -p PROJECT, --project PROJECT
```

#### Watch command

Rebuilds the project on changes.

```
$ python3 statwebgen.py watch -h

usage: statwebgen.py watch [-h] [-i INPUT_FOLDER] [-o OUTPUT_FOLDER]
                           [-p PROJECT]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FOLDER, --in INPUT_FOLDER
                        Input folder
  -o OUTPUT_FOLDER, --out OUTPUT_FOLDER
                        Output folder
  -p PROJECT, --project PROJECT
                        Project to work with
```

#### Serve command

Starts up a development server that automatically reloads on rebuild. Also rebuilds the project on changes. Optionally opens the project in a browser window.

```
$ python3 statwebgen.py serve -h
usage: statwebgen.py serve [-h] [-i INPUT_FOLDER] [-o OUTPUT_FOLDER]
                           [-p PROJECT] [-t PORT] [-r] [-b]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FOLDER, --in INPUT_FOLDER
                        Input folder
  -o OUTPUT_FOLDER, --out OUTPUT_FOLDER
                        Output folder
  -p PROJECT, --project PROJECT
                        Project to work with
  -t PORT, --port PORT  Port to serve on, defaults to 8000
  -r, --autoreload      Automatically refresh browser pages on changes
  -b, --browse          Open the website in the default browser
```

### Dependencies
   * [Python-Markdown](https://pypi.python.org/pypi/Markdown): markdown to html conversion
   * [Jinja2](http://jinja.pocoo.org/): templating
   * [toml](https://pypi.org/project/toml/): front matter