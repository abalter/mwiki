# Installation Instructions

</div>

<div id="contents">

1.  **First edit the script to suit your circumstances:**
    1.  The very first line should read # followed by the path to the Python interpreter
    2.  Amend all the values in the configuration section
        *   **PATH_TO_WIKI_TEXT** = path to where you want to store the plain text version of the pages in your wiki. This can be anywhere that the script has permission to read and write, but somewhere above your htdocs would be sensible, to prevent web users accessing them directly.
        *   **PATH_TO_TEMPLATES** = ditto here - but this where the templates (if you [Define Templates](/MonkeyWiki/DefineTemplates.html)) will go. If you are not using templates, do _not_ leave this blank - put some nonsense (but not the name of a directory obviously!)
        *   **FRONT_PAGE** = The name of the front page of your wiki - 'FrontPage' would do nicely
        *   **NOFOLLOW_OUTLINKS** = 1 (recommended for publicly editable wikis) makes links to pages outside the wiki include the rel="nofollow" attribute which stops people who propagate [Wiki Spam](/MonkeyWiki/WikiSpam.html) from improving the [Page Rank](/MonkeyWiki/PageRank.html) of sites that they link to.
        *   **NUMBERED_OUTLINKS** = 1 for external links to be rendered as numbers, 0 as the URL. See [External Link Options](/MonkeyWiki/ExternalLinkOptions.html)
        *   **REWRITE_MODE** = If this mystifies you, put 0\. Otherwise putting 1, in conjunction with defining [Rewrite Rules](/MonkeyWiki/RewriteRules.html) will make your wiki's URLs look like those of normal pages. Putting 2 will take this a step further, and save static HTML versions of pages for use in between changes - again, this requires that you define [Rewrite Rules](/MonkeyWiki/RewriteRules.html) in addition.
        *   **REWRITE_BASE_URL** = The URL of the directory in which the pages will appear to be by virtue of the rewriting
        *   **EDITABLE** = 0 will make the site impossible to edit, otherwise put 1\. See also [Owner Only Editing](/MonkeyWiki/OwnerOnlyEditing.html)
        *   **BACKUP_ON** = 0 will mean no backups, otherwise put 1
        *   **SMTP_SERVER** = The server to use to send backup copies to you. If in doubt try 'localhost'
        *   **WIKI_LOGGER** = email address from which backups are sent
        *   **WIKI_MASTER** = the address at which you want to receive your backups
        *   **CREDIT** = the credit given to [Monkey Wiki](/MonkeyWiki/MonkeyWiki.html) as the software powering the site. Change to "" if you don't want this to appear
2.  **Now put the script in your cgi-bin (or wherever else you want, if you can run it from there)**
    *   If you are uploading to a server by FTP, make sure you transfer the file as ASCII, not Binary
    *   Make sure the file is set so that it has permission to execute: 755 or 705 are the most likely bets.
3.  **Finally, create the directories that you specified in the configuration section**
    *   (Unless they already exist.) Ideally, they should be created with the minimum permissions possible. However, this rather depends on 'who' your script runs as etc. If the directories are above your htdocs, and your webserver is configured sensibly, this is not too critical.

That's about it - point your browser at the script, or if using Rewrite, at the appropriate URL, and it should work.

Of course until you [Define Templates](/MonkeyWiki/DefineTemplates.html) it will all look a bit bare-bones, but you can do that next...
