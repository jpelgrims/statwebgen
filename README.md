# statwebgen
A simple static website generator, geared towards text-heavy content.

## Usage
The static website is generated in the specified output directory, using the source files found in the input directory. File hierarchy is maintained during conversion.

A new webpage can be added by simply creating a new markdown file in the input directory and adding content. Run the website generator when ready. The markdown in the file will automatically be converted to html and stored in the output directory. Page layout and styling is defined by the page template.

The default page template looks like this:

~~~~html
<!DOCTYPE html>
<html>
    <%head here%>
    <body>
        <%header here%>
        <div class="page-content">
            <%page content here%>
        </div>
        <%footer here%>
    </body>
</html>
~~~~

The `<%page%>` tag is replaced by the markdown file's content (converted to html).