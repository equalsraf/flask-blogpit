"""
Contrib components for blogpit

 - Markdown handlers
"""

from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
from markdown import markdown, Markdown
from BeautifulSoup import BeautifulSoup
from . import ContentHandler
import os

class MarkdownContentHandler(ContentHandler):
    """
    This handler parses stored content as Markdown

    Two simple rules:
    1. Files with extension are served "as-is"
    2. Files without extension are treated as Markdown and used for html pages

    Don't forget to use the |safe template tag to render content.
    """

    def __init__(self):
        pass

    @staticmethod
    def escape_md(rawdata):
        """
        Escape Markdown text, so it won't generate HTML
        """
        html = markdown(rawdata)
        return ''.join(BeautifulSoup(html).findAll(text=True))


    @staticmethod
    def comment_author(form):
        """
        Build a author line form a comment
        """

        prefix = '###{@class=blogpit_comment}'
        name = MarkdownContentHandler.escape_md(form.name.data)
        return u'\n\n%s%s\n' % (prefix, name)

    def filter_articles(self, pathlist):
        """
        This filter rejects:
        - article names with a file extension
        """
        return [ path for path in pathlist if not os.path.splitext(path)[1]]

    def append_comment_from_form(self, rawdata, form, data):
        """
        Arguments:
        + rawdata: is the data as freshly retrieve from the storage
        + form: is the form received by flask
        + data: is the article data as retrieved from the cache

        This method:
        1. Prepends the comment author name as a h3.blogpit_comment element
        2. This prevents comments from injecting HTML into a page using Markdown.
        3. Encodes the result as an utf-8 string

        In practice this does: (Markdown) -> (HTML) -> (Text)
        """

        content = u'%s\n%s' % ( MarkdownContentHandler.comment_author(form),
                MarkdownContentHandler.escape_md(form.content.data))
        return rawdata + content.encode('utf-8')

    def decode(self, path, content):
        """
        Decode content retrieved from the store

        This handler behaves as follows
        1. If the filename has an extension (i.e. "a.png", "file.txt" or "file.")
            then the content is not handled at ALL.
        2. Otherwise the content is decode as utf-8 and converted from
            Markdown to HTML

        The returned structure is a dictionary, holding the following keys
        * content - The html converted content
        * metadata - The metadata retrieved from the store
        * raw - The original content as received before parsing
        """

        if os.path.splitext(path)[1]:
            return content

        raw = content

        md = Markdown( extensions=['meta', 'codehilite', 'fenced_code'],
		    safe_mode=True,
		    )

        content = content.decode('utf-8')
        content = md.convert(content)
        data = {'content' : content, 'metadata' : md.Meta, 'raw' : raw}
        return data

    def get_raw_data(self, data):
        """
        Return a raw version of the given data
        """
        if isinstance(data, basestring):
            return data

        return data.get('raw', '')


