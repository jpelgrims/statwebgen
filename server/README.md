# Development server

A barebones node.js development server that I use for local development in combination with the static website generator. It automatically reloads a page if it changes on disk.

## Usage

```
$ node index.js --help

index.js [command]

Commands:
  index.js serve [port]  Run a development server

Options:
  --help             Show help                                         [boolean]
  --version          Show version number                               [boolean]
  --path, -p         path to a directory to serve                       [string]
  --autorefresh, -r  Automatically reload current page on changes      [boolean]
  --verbose, -v      Run with verbose logging                          [boolean]
```