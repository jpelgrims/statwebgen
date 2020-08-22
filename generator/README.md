# statwebgen
A simple static website generator. I use it for my persal website, found [here](http://www.jellepelgrims.com).

## Features

*   Create static websites from markdown files
*   Jinja2 templating
*   Automatic site rebuilding (no need to rebuild after every change)

### Usage

```
$ python3 statwebgen.py -h

usage: statwebgen.py [-h] [-v] {build,watch} ...

Build static websites.

positional arguments:
  {build,watch}
                        All available subcommands
    build               Build a static website
    watch               Rebuild a static website on changes

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
```

#### Build command

Builds the project.

```
$ python3 generator.py build -h

usage: generator.py build [-h] [-i INPUT_DIR] [-o OUTPUT_DIR] [-t]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --in INPUT_DIR
                        Input directory
  -o OUTPUT_DIR, --out OUTPUT_DIR
                        Output directory
  -t, --testrun         Build the static website without writing to disk (for
                        testing)
```

#### Watch command

Rebuilds the project on changes (only changed files are rebuilt).

```
$ python3 generator.py watch -h

usage: generator.py watch [-h] [-i INPUT_FOLDER] [-o OUTPUT_FOLDER]
                           [-p PROJECT]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FOLDER, --in INPUT_FOLDER
                        Input folder
  -o OUTPUT_FOLDER, --out OUTPUT_FOLDER
                        Output folder
```


### Dependencies
   * [Python-Markdown](https://pypi.python.org/pypi/Markdown): markdown to html conversion
   * [Jinja2](http://jinja.pocoo.org/): templating
   * [toml](https://pypi.org/project/toml/): front matter