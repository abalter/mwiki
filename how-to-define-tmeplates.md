
# How To Define Templates

[Monkey Wiki](/MonkeyWiki/MonkeyWiki.html) templates are HTML files which can contain anything at all that any other web page might contain. Of course that means you can [Use Cascading Style Sheets](/MonkeyWiki/UseCascadingStyleSheets.html), for which [Monkey Wiki](/MonkeyWiki/MonkeyWiki.html) provides certain classes and IDs in its output. So, just fire up your favourite HTML editor and create some pages as you want them to look for the various scenarios described in [What Templates Can Be Defined](/MonkeyWiki/WhatTemplatesCanBeDefined.html). They should be saved _without an extension_, and placed in the template directory specified in the configuration section of the script.

Obviously you don't want to write the actual text of each page, because you are trying to run a dynamic-content site! So, where the actual text from the wiki is to go, you place tokens, which take the general form

    <!--#token-->

These tokens can be _any valid Python expression_, including any variables available within the namespace of the method that renders the page. However you don't need to worry too much about that, because most commonly this will simply be a variable named 'wiki'. This includes a header, contents and footer (just like the page you are reading now)

Thus:

*   `<!--#wiki-->` will place the page's natural output (appropriate to the currect action)

If you don't want to postion the elements of the page in this predefined way, or perhaps want to omit the header or footer, you can place them separately by referring to them instead as 'self.header', 'self.contents' and 'self.footer'.

*   `<!--#self.header-->` will place just the header (the bit that conatins name of the page as above)
*   `<!--#self.contents-->` will place just the contents of the page, without heading or footer
*   `<!--#self.footer-->` will place just the footer of the page (contains the Edit, Rename... links)

You can also get at various other attributes of the page, including its name, title, filename etc. These are referenced in the following way: 'self.page', 'self.title', 'self.textfile'
Thus:

*   `<!--#self.page-->` will place the page's name
*   `<!--#self.title-->` will place the page's title (same as 'page' but with spaces)
*   `<!--#self.textfile-->` will place the name of the text file where the page's contents are stored.

You will probably want to put either self.page or self.title inside <title></title> tags in the template (up in the HTML <head></head> section).

Here is an example of how you might want to use self.textfile - this shows when the file was last modified:

    <!--#time.ctime(path.getmtime(self.textfile))-->

(If you don't know Python, just copy this exactly!)

To include the content (contents only) of another page within the wiki (called 'OtherPage' in the following example), use the following form:

    <!--#WikiPage('OtherPage')-->

Environment variables can be included using the following form (using SCRIPT_NAME as an example here):

    <!--#os.environ["SCRIPT_NAME"]-->

Advanced users can examine the code to see what other expressions might be possible, but obviously care is required, for example to avoid infinitely recursive inclusions.

Any token which is not successfully evaluated is ignored.
