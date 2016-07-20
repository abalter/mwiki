What Templates Can Be Defined
=============================

The following kinds of templates, which are described on this page, can be defined:

-   Action-specific templates
-   Page-specific templates
-   A default template

### Action-specific templates

<a href="/MonkeyWiki/MonkeyWiki.html" class="wikilink">Monkey Wiki</a> always calls a page with one of the following ‘actions’:

-   **goto** - just display the page
-   **edit** - edit the page (via an edit screen)
-   **rename** - rename the page (via a screen requesting the new name)
-   **delete** - delete the page (via a screen requesting confirmation)
-   **likesearch** - show pages including words from the current title
-   **backsearch** - show pages referencing the current one
-   **localmap** - show forward links *from* the current page, plus links from *those* pages and so on, in the form of a ‘tree’

All the actions except ‘goto’ can have a template named after them. (If you define one called ‘goto’ it will be ignored). Thus you may want a different layout for the edit screen, a violent red and black background for the delete screen etc.

### Page-specific templates

You can define a template for use with a specific page by giving it the same name as that page. You can have as many of these as you like. This type of template will only be used for the ‘goto’ action - i.e. when the page itself is displayed.

Note: If a page is renamed, any corresponding template is *not* automatically renamed. (*Discussion point: if the site owner has gone to the trouble of defining a template for a particular page, should it be impossible to rename it? Not difficult to code, by is it desirable?*)

### A default template

You should define at least this template and name it ‘default’. This will be used if no action template is defined for the current action or page.

### Typical usage

A typical setup might be to have the following templates:

-   Front `<!--  -->` Page
-   edit
-   delete
-   default

This way, you can have a distinctive Front<!--  -->Page, a special layout for editing (to accommodate the text box nicely for example), a special page for delete which might have heavy-duty warnings etc, and a default template to define the look for the rest of the wiki.

If you define no templates at all, you will have a perfectly functional, but bare-bones representation.

On to <a href="/MonkeyWiki/HowToDefineTemplates.html" class="wikilink">How To Define Templates</a>;
