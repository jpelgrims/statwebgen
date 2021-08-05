   
# Statwebgen

## Proposed features

* Add search capability (javascript) as an addon possible for every webpage. It should have suggestions with previews. Search indexes can be built during website generation and served along with the rest of the content, so that the javascript search widget can make use of it.
* Add functionality of mkdocs (themes, 'mkdocs.yml' config file, javascript search)
* Define which variables are passed into the template engine (i.e. site varaibles, page variables, ...), see https://jekyllrb.com/docs/variables/
* Add draft switch to page front-matter, if switch on then don't publish page
  * Add drafts option to build command (so drafts are also included in the build)
* Simply run statwebgen without any arguments to build & serve current folder
* Run any command wihtout any arguments to wokr in the current directory (i.e. `statwebgen serve` will serve the contents of the current directory)
* See https://squidfunk.github.io/mkdocs-material/ for theme
* Add scanning/linting functionality, e.g. to look for missing metadata tags or broken links