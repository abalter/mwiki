#!/usr/bin/python

''' MonkeyWiki: A simple wiki engine
    Copyright (C) 2005 Barnaby Scott <bds@waywood.co.uk>
    http://www.waywood.co.uk/MonkeyWiki

    Version 1.05

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA'''

import cgi, re, os, sys, time
from os import path

try:
    import mwmacros
except:
    pass

#==CONFIGURATION SECTION===========================================================================
PATH_TO_WIKI_TEXT = '/path/to/wiki/text/files/'
PATH_TO_TEMPLATES = '/path/to/wiki/template/files/'
FRONT_PAGE = 'FrontPage' #required, must be WikiName. (= name of 'top' or 'home' page)
NOFOLLOW_OUTLINKS = 1
NUMBERED_OUTLINKS = 1
REWRITE_MODE = 0
REWRITE_BASE_URL = ''
EDITABLE = 0
BACKUP_ON = 0 #use the backup feature? (backups are done by email)
SMTP_SERVER = 'localhost'
WIKI_LOGGER = 'wikilogger@your.domain' #email address from which backups are sent
WIKI_MASTER = 'wikimaster@your.domain' #email address to which backups are sent
CREDIT = 'Site powered by <a href="http://www.waywood.co.uk/MonkeyWiki/">MonkeyWiki</a>'
#==================================================================================================

class WikiName:
    re = '(?:[A-Z][a-z]+)+(?:(?:[A-Z][a-z]+)|[0-9]+)'
    #re = '(?:[A-Z][a-z]+){2,}' #strict CamelCase - swap commenting with above line to revert
    
    def __init__(self, name):
        self.name = name
        
    def is_valid(self):
        return re.match('^%s$' % self.re, self.name) is not None

    def spacify(self):
        return re.sub('([a-z])([A-Z0-9])', r'\1 \2', self.name)

class WikiParser:
    '''
    class whose instances behave like a function to turn text with wiki 'mark-up' into HTML,
    or rather, XHTML now
    '''
    #the main regular expression to recognise wiki 'mark-up'
    main_re = re.compile(
        r'(?P<empty_line>^\r\s*$)'                      #}
        + r'|(?P<list>^\r\s+[*#]?)'                     #}all these plus para_start
        + r'|(?P<heading>^\r(?P<u>_{2,6}).+(?P=u)\s*$)' #}we know will not be picked
        + r'|(?P<rule>^\r-{4,}\s*$)'                    #}up if we are in a pre block
        + r'|(?P<clear>^\r\\{2}\s*$)'                   #}notice the ^\r beginnings
        + r'|(?P<lonemacro>^\r\[\[.*?\]\]\s*$)'         #}
        + r'|(?P<para_start>^\r)'   #must be last linestart-dependent re (block element)
        + r'|(?P<pre>\{\{|\}\})'
        + r'|(?P<macro>\[\[.*?\]\])'
        + r'|(?P<emph>\'{2,3})'
        + r'|(?P<wiki>\b%s\b)' % WikiName.re
        + r'|(?P<image>(\b|[|])((http\://)|(www\.))[-\w./~%]+((\.jpe?g)|(\.JPE?G)|(\.gif)|(\.GIF)|(\.png)|(\.PNG))([|]|\b))'
        + r'|(?P<url>(https?|ftp|nntp|news)\://[-\w./~?=&+%#]+[\w/])'
        + r'|(?P<www>www\.[-\w./~?=&+%#]+[\w/])'
        + r'|(?P<email>(mailto:)?[-\w.+]+@[a-zA-Z0-9\-.]+[a-zA-Z])'
        )    
    
    def __init__(self):        
        self.tagqueue, self.recyclequeue = [], []
        self.clear_margins = False
        self.linkref = 1
                        
    def _empty_line_repl(self, s):          
        return self.closetags(recycle=['em','strong'], ruthless=True) 

    def _list_repl(self, s):
        s = s[1:]   #ditch the opening \r
        listtype, itemtag, level = {'*': ('ul', 'li', len(s) - 1),
                                     '#': ('ol', 'li', len(s) - 1)}.get(
                                         s[-1],('blockquote', 'p', len(s)))
        d_level = level - (self.tagqueue.count('ul') + self.tagqueue.count('ol')
                             + self.tagqueue.count('blockquote'))
        #get rid of open <p> if present (either within a blockquote or directly in body)
        r = self.closetags(['p'], ['em','strong'])
        #prepare for adding list item, by changing to new level or simply closing last item
        if d_level > 0:
            if listtype == 'blockquote':
                r += '\n' + self.opentags([listtype] * d_level)
            else:
                r += '\n' + self.opentags([listtype, itemtag] * (d_level - 1) + [listtype])
        elif d_level < 0:
            r += self.closetags(['ol', 'ul', 'blockquote'], ['em','strong'], True, abs(d_level))
            r += self.closetags([itemtag], ['em','strong'], False, 1)
        else:
            r += self.closetags([itemtag], ['em','strong'], False, 1)
        #if list is of the wrong type at this level, change it:
        if listtype != [i for i in self.tagqueue if i in ('ol', 'ul', 'blockquote')][-1]:
            r += self.closetags(['ol', 'ul', 'blockquote'], ['em','strong'], True, 1)
            r += '\n' + self.opentags([listtype], False)
        #now add item tag (& recycled tags if necessary)    
        r += '\n' + self.opentags([itemtag], True)   
        #return result
        return self.do_clear(r)

    def _heading_repl(self, s):
        s = s.strip()
        text = s.strip('_')
        hlevel = (len(s) - len(text))/2
        r = self.closetags(recycle=['em','strong'], ruthless=True)
        r += '\n<h%s>%s</h%s>' % (hlevel, text, hlevel)
        return self.do_clear(r)
        
    def _rule_repl(self, s):
        r = self.closetags(recycle=['em','strong'], ruthless=True) + '\n<hr />'
        return self.do_clear(r)

    def _clear_repl(self, s):
        self.clear_margins = True
        return self.closetags(recycle=['em','strong'], ruthless=True)

    def _para_start_repl(self, s):
        if 'p' in self.tagqueue and 'blockquote' not in self.tagqueue:
            r = '<br />\n'
        else:
            r = self.closetags(recycle=['em','strong'], ruthless=True)\
                + '\n' + self.opentags(['p'], True)
        return self.do_clear(r)

    def _lonemacro_repl(self, s):
        '''for macro calls that appear alone on a line and do not want block-level management
        e.g. the macro inserts some content in its own <div>
        the clearance of margins is *not* attempted (because the contents of the macro's output
        is unknown) so any pending request to clear margins is deferred'''
        r = self.closetags(recycle=['em','strong'], ruthless=True) + self._macro_repl(s.strip())
        return r

    def _pre_repl(self, s):
        if s == '{{' and 'pre' not in self.tagqueue:
                self.pre_in_p = 'p' in self.tagqueue
                r = self.closetags(['p'], ['em','strong'])
                r += self.opentags(['pre'], True)
        elif s == '}}' and 'pre' in self.tagqueue:
                r = self.closetags(['pre'], recycle=['em','strong'])
                if self.pre_in_p:
                    self.recyclequeue.insert(0, 'p')
                r += self.opentags([], True)                
        else:
            r = s
        return r
    
    def _macro_repl(self, s):
        try:
            r = eval('mwmacros.%s' % s[2:-2])
        except:
            r = self._comment_repl(s)
        return r
   
    def _comment_repl(self, s):
        if s.count('--'):   #likely to be invalid comment
            r = s
        else:
            r = '<!-- %s -->' % s[2:-2]
        return r
   
    def _emph_repl(self, s):
        this_tag, other_tag = (('em', 'strong'), ('strong', 'em'))[len(s)-2]
        r = ''
        if this_tag in self.tagqueue:
            r += self.closetags([this_tag], [other_tag], False, 1)
            r += self.opentags([], True) #reopen other tag if nece
        else:
            r = self.opentags([this_tag])
        return r

    def _wiki_repl(self, s):
        w = WikiPage(s)
        if w.existcode:
            r = '<a class="wikilink" href="%s">%s</a>' % (cgi.escape(w.get_href()), w.title)
        else:
            r = '%s<a class="nonexistent" href="%s">?</a>' % (s, cgi.escape(w.get_href()))
        return r
    
    def _image_repl(self, s):
        src = s.strip('|')
        if src[:7] != 'http://':
            src = 'http://' + src
        if 'pre' in self.tagqueue:
            r = self._url_repl(src)
        else:
            i = 'img src="%s" alt="%s"' % (src, src)
            if (s[0], s[-1]) == ('|', '|'):
                r = self.closetags(recycle=['p', 'em', 'strong'])
                r += '<div style="text-align:center;"><%s /></div>' % i
                r += self.opentags([], True)
            elif s[0] == '|':
                r = '<%s style="float:left;padding-right:20px;" />' % i
            elif s[-1] == '|':
                r = '<%s style="float:right;padding-left:20px;" />' % i
            else:
                r = '<%s style="padding-left:20px;padding-right:20px;" />' % i
        return r

    def _url_repl(self, s):
        rel = ('', ' rel="nofollow"')[NOFOLLOW_OUTLINKS]
        if NUMBERED_OUTLINKS:
            displaytext = '[%s]' % self.linkref
            self.linkref += 1
        else:
            displaytext = s
        return '<a href="%s"%s>%s</a>' % (cgi.escape(s), rel, displaytext)

    def _www_repl(self, s):
        return self._url_repl('http://' + s)

    def _email_repl(self, s):
        if s[:7] == 'mailto:':
            href = s
        else:
            href = 'mailto:' + s
        return '<a href="%s">%s</a>' % (href, s)

    def closetags(self, tags=[], recycle=[], ruthless=False, count=None):
        '''Closes tags according to the following rules
        1. Tags closed will be those contained in the tags parameter, which is a list, subject to
        the effects of other parameters. If tags is omitted, any tag may be closed
        2. 'recycle' (optional) is a list of tags which, if encountered, will be closed but
        recorded in a separate list so the they can be reopened when appropriate
        3. 'ruthless' (boolean, optional) controls whether tags that are met before those nominated
        in 'tags' or 'recycle', are closed. If false (default) the function will terminate when a
        tag not named in either 'tags' or 'recycle' is encountered, potentially leaving some
        specified tags *un*closed 
        4. count (int, optional) determines the maximum number of tags appearing in 'tags' that
        will be closed. If 'tags', is omitted, all tags closed will be governed by this number.
        Otherwise, the action on tags appearing only in recycle is *not* governed by this number.
        '''
        r, no_closed = '', 0
        while self.tagqueue and (no_closed<count or count==None):
            if [i for i in (tags + recycle) if i in self.tagqueue] or tags==[]:
                last_tag = self.tagqueue[-1]
                if last_tag in (tags + recycle) or ruthless == True:                
                    if last_tag in recycle:
                        self.recyclequeue.insert(0, last_tag)
                    r += '</%s>' % (self.tagqueue.pop())
                    if last_tag in tags or tags==[]:
                        no_closed += 1
                else:
                    break
            else:
                break
        return r

    def opentags(self, tags, openrecycled=False):
        r = ''
        if openrecycled:
            tags += self.recyclequeue
            self.recyclequeue = []
        for i in tags:
            r += '<%s>' % i
            self.tagqueue.append(i)        
        return r
        
    def do_clear(self, s):
        '''places a style attribute in the first available html tag which, by the context in which
        this method is called, we know will be an *opening* block-level tag'''
        if self.clear_margins:
            r = re.sub(r'((?: /)?>)', r' style="clear:both;"\1', s, 1)
            self.clear_margins = False
        else:
            r = s
        return r        

    def replace(self, match):
        'calls appropriate helper (based on named RE group) to replace each type of token'
        tokentype = match.lastgroup
        token = match.groupdict()[tokentype]
        return getattr(self, '_' + tokentype + '_repl')(token)

    def __call__(self, text):
        'main HTML formatter function'
        html = ''
        
        if text.strip():
            #turn all traces of HTML tags into readable, non-functional versions
            text = cgi.escape(text, 1)
            #start
            for line in text.splitlines():
                #put in \r or \n line beginnings as part of the recognition for block-level element 
                #tags, depending on whether we are inside a <pre> block at this point. If we're not,
                #the \r will be found and transformed into \n + appropriate block level element tag
                #(or blank line). Otherwise, \n will be left to be expressed inside <pre> block.
                line = ('\r', '\n')['pre' in self.tagqueue] + line
                #main substitution call
                html += re.sub(self.main_re, self.replace, line)
                
            #remove redundant markup left over from correct nesting enforcement for emphasis tags
            html = html.replace('<em></em>', '')
            #close any tags left open & reset state variables for next use
            html += self.closetags(ruthless=True)   
            self.__init__()                         

        return html


class WikiPage:
    def __init__(self, page, action='', **otherparams):
        self.__dict__ = otherparams
        wn = WikiName(page)
        assert wn.is_valid(), 'Invalid WikiName'
        self.page = wn.name
        self.title = wn.spacify()
        self.textfile = path.join(PATH_TO_WIKI_TEXT, page)
        if hasattr(AutoPage, page):          
            self.existcode = 2  #special auto-generated page
            self.action = action.lower() or 'goto'
            self.ok_actions = ['goto', 'likesearch', 'backsearch']
        elif os.path.isfile(self.textfile):
            self.existcode = 1  #physically existing page
            self.action = action.lower() or 'goto'
            self.ok_actions = ['goto', 'edit', 'rename', 'delete', 'likesearch', 'backsearch','localmap']
        else:                               
            self.existcode = 0  #non-existent (new) page
            self.action = action.lower() or 'edit'
            self.ok_actions = ['edit', 'likesearch','backsearch','localmap']
        if not EDITABLE:
            self.ok_actions = [i for i in self.ok_actions if i not in ['edit', 'rename', 'delete']]
        self.HTMLfile = path.join(os.getenv('DOCUMENT_ROOT'),
                                  REWRITE_BASE_URL.lstrip('/'), page + '.html')
        self.cache_me = 0 #only for internal use
        
    def __str__(self):
        if self.existcode == 2:
            r = str(AutoPage(self))
        else:
            r = htmlize(self.get_text())
        return r

    def goto(self, message=''):
        if message:
            msgstr = '<p class="message">%s</p>' % message
        else:
            msgstr = ''
            if REWRITE_MODE == 2 and self.existcode == 1: self.cache_me = 1
        return msgstr + str(self)

    def edit(self):
        save = getattr(self, 'save', '')
        if save != 'Save':
            r = '''<form method="post" action="%s">
            <p><input type="hidden" name="page" value="%s" />
            <input type="hidden" name="action" value="edit" />
            <textarea name="newtext" rows="17" cols="80">%s</textarea><br />
            <input type="submit" value="Save" name="save" />
            <input type="reset" value="Reset" /></p></form>
            ''' % (os.getenv('SCRIPT_NAME'), self.page, cgi.escape(self.get_text(), 1))
        else:
            assert os.getenv('REQUEST_METHOD') == 'POST', 'Only POST allowed'
            #next 2 lines create version of self.newtext ensuring LF linebreaks
            newlines = getattr(self, 'newtext', '').splitlines(False)
            newtext = '\n'.join(newlines)
            if not newtext.strip():             #new text is nil or just space
                r = self.delete()
            elif newtext != self.get_text():    #new text exists and is different from old text
                self.kill_HTMLfile()
                self.refresh_dependents()
                self.backup()
                file(self.textfile,'w').write(newtext)
                self.__init__(self.page)
                r = self.goto('Thank you for your update')
            else:                               #new text is the same as old text
                self.__init__(self.page)
                r = self.goto()
        return r

    def delete(self):     
        confirmdelete = getattr(self, 'confirmdelete', '')
        if not confirmdelete:
            r = '''<form method="post" action="%s">
            <p>Do you really want to delete page '%s'?
            <input type="hidden" name="page" value="%s" />
            <input type="hidden" name="action" value="delete" /></p>
            <p><input type="radio" name="confirmdelete" value="Yes" /> Yes<br />
            <input type="radio" name="confirmdelete" value="No" checked="checked" /> No</p>
            <p><input type="submit" value="Submit" name="submit" /></p></form>
            '''% (os.getenv('SCRIPT_NAME'), self.title, self.page)
        elif confirmdelete == 'Yes':
            assert os.getenv('REQUEST_METHOD') == 'POST', 'only POST allowed'
            self.kill_HTMLfile()
            self.refresh_dependents()
            self.backup()
            os.remove(self.textfile)
            msg = "The page '%s' has been deleted" % self.title
            self.__init__(FRONT_PAGE)
            r = self.goto(msg)
        else:
            self.__init__(self.page)
            r = self.goto()
        return r
        
    def rename(self):
        newname = getattr(self, 'newname', '')
        if not WikiName(newname).is_valid(): #including of course if newname==''
            r = '''<form method="post" action="%s">
            <p>New name for '%s' (enter in WikiName format):<br />
            <input type="text" name="newname" size="20" />
            <input type="hidden" name="page" value="%s" />
            <input type="hidden" name="action" value="rename" />
            <input type="submit" value="Submit" />
            <input type="reset" value="Reset" /></p></form>
            '''% (os.getenv('SCRIPT_NAME'), self.page, self.page)
        else:
            assert os.getenv('REQUEST_METHOD') == 'POST', 'only POST allowed'
            ren_wp = WikiPage(newname)
            if ren_wp.existcode:
                raise Exception, 'Cannot overwrite %s page'\
                      % ('existing', 'automatic')[ren_wp.existcode - 1]
            else:
                self.kill_HTMLfile()
                self.refresh_dependents()
                self.backup()
                os.rename(self.textfile, ren_wp.textfile)
                #amend refering pages to show the new name
                for page in self.get_referers():
                    w = WikiPage(page)
                    changedtext = re.sub(r'\b%s\b' % self.page, newname, w.get_text())
                    file(w.textfile,'w').write(changedtext)
                msg = "The page '%s' has been renamed to '%s'" % (self.title, ren_wp.title)
                self.__init__(newname)
                r = self.goto(msg)
        return r
        
    def likesearch(self):
        self.searchtext = self.title.replace(' ', '|') 
        return AutoPage(self).SiteSearch()
                               
    def localmap(self):
        return AutoPage(self).SiteMap(self.page)
        
    def backsearch(self):
        return htmlize("__Pages referring to '%s'__\n *%s" %\
                       (self.title, '\n *'.join(self.get_referers()) or '[None]'))

    def backup(self):
        if not BACKUP_ON: return

        import smtplib, email.MIMEMultipart, email.MIMEText
        notification = "At %s, %s %sed '%s'" % (
            time.ctime(), os.getenv('HTTP_X_FORWARDED_FOR', os.getenv('REMOTE_ADDR', '[unknown]')),
            self.action.rstrip('e'), self.page)

        if self.action == 'rename':
            notification += " to '%s'" % self.newname
            m = email.MIMEText.MIMEText(notification)
        else:
            att = email.MIMEText.MIMEText(self.get_text())
            att.add_header('Content-Disposition', 'attachment', filename=self.page)
            m = email.MIMEMultipart.MIMEMultipart()
            m.attach(email.MIMEText.MIMEText(notification))
            m.attach(att)
            m.epilogue = ''

        m['From'],m['To'],m['Subject'] = WIKI_LOGGER,WIKI_MASTER,'%s %s'%(self.page, self.action)

        server = smtplib.SMTP(SMTP_SERVER)
        server.sendmail(WIKI_LOGGER, [WIKI_MASTER], m.as_string())
        server.quit()

    def get_text(self):
        return eval(('"Type your text here"', "file(self.textfile).read()", '""')[self.existcode])
              
    def get_href(self):
        if REWRITE_MODE and self.action == 'goto':
            r = path.join(REWRITE_BASE_URL, self.page + '.html')
        else:
            r = '%s?page=%s' % (os.getenv('SCRIPT_NAME'), self.page)
            if self.action != 'goto':
                r += '&action=' + self.action
        return r
    
    def get_referers(self):
        p = re.compile(r'\b%s\b' % self.page)
        r = [i for i in getwikipagelist() if p.search(WikiPage(i).get_text())]
        r.sort()
        return r

    def get_includers(self):
        p = re.compile(r'\b%s\b' % self.page)
        includer_templates = [i for i in os.listdir(PATH_TO_TEMPLATES)
                              if p.search(file(path.join(PATH_TO_TEMPLATES, i)).read())]
        r = []
        for i in includer_templates:
            if i == 'default':
                r = getwikipagelist()
                break
            elif WikiName(i).is_valid():
                r.append(i)
        return r

    def kill_HTMLfile(self):
        if REWRITE_MODE == 2 and path.isfile(self.HTMLfile):
            os.remove(self.HTMLfile) #if fails, allow exception

    def refresh_dependents(self):
        if REWRITE_MODE == 2:
            for page in self.get_referers() + self.get_includers():
                WikiPage(page).kill_HTMLfile()

    def do_action(self):
        assert self.action in self.ok_actions, 'You may not %s this page' % self.action        
        #contents - do this first, as it affects the nature of the other components
        self.contents = '<div id="contents">%s</div>' % getattr(self, self.action)()
        #template - set up longstop template, then overwrite it if a user-defined one is found
        self.template = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/2002/REC-xhtml1-20020801/DTD/xhtml1-strict.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head><title><!--#self.title--></title>
        <style type="text/css">
        #header {border-bottom-width: 2px; border-bottom-style: groove;}
        #footer {border-top-width: 2px; border-top-style: groove; clear:both;}
        </style></head>
        <body><!--#wiki--></body></html>'''
        for i in [(self.action, self.page)[self.action == 'goto'], 'default']:
            try:
                self.template = file(path.join(PATH_TO_TEMPLATES, i)).read()
                break
            except: pass              
        #header
        if self.action == 'goto':
            self.header = '<div id="header"><h1>%s</h1></div>' % self.title
        else:
            self.header = '<div id="header"><h1>\'%s\': %s</h1></div>' % (self.title, self.action.capitalize())
        #footer
        pagelinks = ' | '.join(
            ['<a href="%s">%s</a>' % (cgi.escape(WikiPage(self.page, i).get_href()), i.capitalize())
             for i in self.ok_actions if i != self.action])
        sitelinkpages = [WikiPage(i) for i in
                         [FRONT_PAGE] + dir(AutoPage) if WikiName(i).is_valid() and i != self.page]
        sitelinks = ' | '.join(
            ['<a href="%s">%s</a>' % (cgi.escape(i.get_href()), i.title) for i in sitelinkpages])
        self.footer = '<div id="footer">%s<br />%s<p id="credit">%s</p></div>'\
                      % (pagelinks, sitelinks, CREDIT)

    def web_output(self):
        self.do_action()
        wiki = '\n'.join([getattr(self, i) for i in ['header', 'contents', 'footer']])

        def evaltext(m, g=globals(), l=locals()):
            try: return str(eval(m.group(1), g, l))
            except: return m.group(0)
        r = re.sub(r'<!--#(.+?)-->', evaltext, self.template)

        if self.cache_me:
            file(self.HTMLfile, 'w').write(r)

        return r
    
class AutoPage:
    '''Provide automatically generated content for certain pages. The existence of a suitably
    named method here (must be a WikiName) defines that page as being an auto-generated one'''
    
    def __init__(self, wikipage):
        self.wikipage = wikipage        

    def SiteMap(self, top_page=None):
        def mapchildren(page, indent):
            pagechildren = re.findall(r'\b%s\b' % WikiName.re, WikiPage(page).get_text())
            for child in pagechildren:
                if child in unmappedpages:
                    self.autotext += '%s*%s\n' %(' ' * indent, child)
                    unmappedpages.remove(child)
                    mapchildren(child, indent + 1)
                elif WikiPage(child).existcode == 0 and child not in wantedpages:
                    wantedpages.append(child)
        top_page = top_page or FRONT_PAGE
        wantedpages = []
        unmappedpages = [i for i in getwikipagelist() if i != top_page]
        self.autotext = '__Tree of pages, starting from %s__\n *%s\n' % (top_page, top_page)
        mapchildren(top_page, 2)
        unmappedpages.sort()
        self.autotext += '__Pages outside tree__\n *'\
                         + ('\n *'.join(unmappedpages) or '[None]') + '\n'
        wantedpages.sort()
        self.autotext += '__Wanted pages__\n *'\
                         + ('\n *'.join(wantedpages) or '[None]') + '\n'
        return htmlize(self.autotext)
                
    def SiteSearch(self):
        searchtext = getattr(self.wikipage, 'searchtext', '')
        if searchtext:
            titlehits, texthits = [], []
            for page in getwikipagelist():
                p = re.compile(searchtext, re.I + re.M)
                w = WikiPage(page)
                titlehits.append((w.page, p.search(w.title)))
                texthits.append((len(p.findall(w.get_text())), w.page))
            titlehits.sort()
            texthits.sort(); texthits.reverse()
            self.autotext = '''__Matches for: %s__\n___Title matches___\n *%s\n----
            \n___Text matches (& number of matches)___\n *%s
            ''' % (searchtext, '\n *'.join([i[0] for i in titlehits if i[1]]) or '[None]',
                   '\n *'.join(['%s (%s)' % (i[1], i[0]) for i in texthits if i[0]]) or '[None]')
        else:
            self.autotext = '__New Search__'
        return htmlize(self.autotext) + '''<form method="get" action="%s">
        <p>Search for: 
        <input type="hidden" name="page" value="SiteSearch" />
        <input type="text" name="searchtext" value="%s" size="20" />
        <input type="submit" value="Submit" />
        <input type="reset" value="Reset" /></p></form>
        ''' % (os.getenv('SCRIPT_NAME'), cgi.escape(searchtext, 1)) 

    def RecentChanges(self):
        modlist = [(path.getmtime(path.join(PATH_TO_WIKI_TEXT, i)), i) for i in getwikipagelist()]
        modlist.sort(); modlist.reverse()
        modlist = modlist[:50]
        self.autotext = '{{' + '\n'.join([time.ctime(i[0]) + '   ' + i[1] for i in modlist]) + '}}'
        return htmlize(self.autotext)

    def __str__(self):
        return getattr(self, self.wikipage.page)()
    
                                 
def get_wp_args():
    argdict = {'page': FRONT_PAGE} #default

    form = cgi.FieldStorage()
    for k in form.keys():
        argdict[k] = form[k].value

    return argdict


def getwikipagelist():
    return [i for i in os.listdir(PATH_TO_WIKI_TEXT)\
            if path.isfile(path.join(PATH_TO_WIKI_TEXT, i)) and WikiName(i).is_valid()]


def main():
    print 'Content-Type: text/html; charset=iso-8859-1\n'
    try:
        wikipage = WikiPage(**get_wp_args())
        #set environment variable for use by any ancillary scripts (e.g. macros)
        #that might require a route back to the current wiki page 
        os.environ['WIKIPAGE_URI'] = 'http://%s%s' % (
            os.environ['SERVER_NAME'],
            WikiPage(wikipage.page, 'goto').get_href())
        #emit full wiki page
        print wikipage.web_output()
    except Exception, inst:
        print 'Error:', inst

htmlize = WikiParser()

if __name__ == '__main__': main()

