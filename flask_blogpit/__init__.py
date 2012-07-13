# -*- coding: utf-8 -*-
"""
flask_blogpit

Blogpit storage for markdown

To use:

    app.register_blueprint( 
            create_blogpit_blueprint('/srv/git/source.git',
                'refs/heads/master', None,
                ContentHandler))

"""
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
from flask import Blueprint, render_template, abort, request, redirect, \
                    url_for, flash, current_app


BLOGPIT_COMMENT_MSG_TEMPLATE = """%s

Referer: %s
Remote addr: %s
Language: %s
User Agent: %s
"""

from blogpit import Blogpit
import mimetypes
import os
from BeautifulSoup import BeautifulSoup
#import forms
from .forms import CommentForm

class ContentHandler(object):
    """
    This class intercepts all operations involving
    data coming from, or going to the blogpit storage.
    This involves:
    1. Reading content
    2. Storing content

    """

    def filter_sections(self, pathlist):
        """
        Filter out sections you don't want to be visible

        This method takes a list of paths and returs a
        subset of the given list - removing those that should
        be concealed from lists.

        This implementation returns the given list as is.
        """

        return pathlist

    def filter_articles(self, pathlist):
        """
        Filter out articles you don't want to be visible

        This method takes a list of paths and returs a
        subset of the given list - removing those that should
        be concealed from lists.

        This implementation returns the given list as is.
        """
        return pathlist

    def decode(self, path, content):
        """
        Decode byte content as retrieved from the store
        and if need be, convert it.

        The outcome of this method is what you will get in templates, so
        act accordingly. If the result of this call is a byte string (str)
        them blogpit will serve directly as static content, otherwise this
        will be passed upwards into the proper template.

        This particular implementation decodes ALL content as utf-8
        and returns an unicode object
        """

        return content.decode('utf-8')

    def append_comment_from_form(self, rawdata, form, data):
        """
        Given a comment form convert it into some data we safely store away.
        Return a new version to be stored, based on the current rawdata plus
        the data extracted from the form.

        This method should:
        1. Append information that identifies the owner of the comment
        2. Escape comment content
        3. Return a string object

        This particular implementation:
        1. Prepends the message with the author name
        2. <Does nothing to escape the content>
        3. Encodes the result as an utf-8 string
        """

        name_esc = ''.join(BeautifulSoup(form.name.data).findAll(text=True))
        content_esc = ''.join(BeautifulSoup(form.name.data).findAll(text=True))

        content = u'\n<br/>%s<br/>\n%s' % (name_esc, content_esc)
        return rawdata + content.encode('utf-8')

    def get_raw_data(self, data):
        """
        Return a raw version of the given data

        In this implementation we store the raw data directly, so this method
        just returns the same data
        """
        return data

def create_blogpit_blueprint(path, branch, cache, handler, use_debugpit, **kwargs):
    """
    Bluepring factory for blogpit

    * path - the repository database path
    * branch - the repository branch references, e.g. refs/heads/master
    * cache - a cache object i.e. a SimpleCache or MemcacheCache
    * handler - a blogpit content hander - or None for a default raw handler
    * use_debugpit - If True we will load data from a workdir instead of the repo
    """
    __cache = cache

    if use_debugpit:
        from .contrib import DebugPit
        blogpit_cls = DebugPit
    else:
        blogpit_cls = Blogpit

    __blogpit = blogpit_cls(path, branch)

    if handler:
        __handler = handler
    else:
        __handler = ContentHandler()


    name = 'blogpit-' + str(id(__blogpit))
    blogpit_blueprint = Blueprint(name, __name__, 
                                template_folder='templates', **kwargs)

    def from_cache(fun):
        """
        A decorator to cache function results.

        All decorated functions must take a single argument, a path.
        """
        def newfun(path):
            if not __cache:
                return fun(path)

            key = '%s:%s:%s' % (fun.func_name, __blogpit.version(), path)
            data =  __cache.get(key)
            if data is None:
                data = fun(path)
                __cache.set(key, data)
            return data

        return newfun

    @from_cache
    def getarticle(path):
        """
        Get content
        """
        raw = get_article_from_store(path)
        if not raw:
            return raw
        return __handler.decode(path, raw)

    def get_article_raw(path):
        """
        Get raw version of data
        """

        data = getarticle(path)
        return __handler.get_raw_data(data)


    def get_article_from_store(path):
        """
        Get content - skipping cache and content handler
        """
        r = __blogpit.getarticle(path)
        return r

    @from_cache
    def sections(path):
        return  __handler.filter_articles( __blogpit.sections(path))
    @from_cache
    def articles(path):
        return  __handler.filter_articles( __blogpit.articles(path) )

    @blogpit_blueprint.context_processor
    def blogpit_menu(path=''):
        """
        A context process to insert a list of sections
        """
        return dict(blogpit_menu=sections(path))

    @blogpit_blueprint.route('/', defaults={'path' : ''})
    @blogpit_blueprint.route('/<path:path>', methods=['GET', 'POST'])
    def blogpit_content(path):
        """
        Load a page from blogpit

        1. If an articles exists, loads an article
        2. If this is a POST, add the comment
        3. Otherwise load a section or 404
        4. If a section exists but has only one article - load that in its
           place

        """

        rss = os.path.basename(path) == 'rss'

        # Section
        if not path or path.endswith('/') or rss:

            if rss:
                realpath = path
                path = os.path.dirname(path) + '/'

            section_names = sections(path)
            article_names = articles(path)

            if not section_names and not article_names:
                abort(404)
            elif not section_names and len(article_names) == 1:
                if rss:
                    abort(404)
                else:
                    path += article_names[0]
            else:
                article_names.sort(reverse=True)
                section_names.sort()

                items = {}
                for name in article_names:
                    items[name] = getarticle(os.path.join(path, name))


                if rss:
                    result = render_template('blogpit/rss.xml', article_names=article_names,
                                                articles=items,
                                                blogpit_path=path)
                    return current_app.response_class(result, mimetype='application/rss+xml')


                return render_template('blogpit/section.html', article_names=article_names,
                                            articles=items,
                                            sections=section_names, blogpit_path=path)

        data = getarticle(path)
        if not data:
            # This should never happen
            abort(404)

        # Binary data is sent out immediatly
        if isinstance(data, str):
            mimetype = mimetypes.guess_type(path)[0]
            return current_app.response_class(data,mimetype=mimetype,direct_passthrough=False)

        # If we find spam in comments, we
        # disable the comment form (see bellow)
        # This flags is inserted in the template dict
        spam_found = False

        # Article
        if current_app.config.get('BLOGPIT_COMMENTS', False):
            form = CommentForm(request.form)
            if form.validate_on_submit():
                rawdata = get_article_from_store(path)
                newdata = __handler.append_comment_from_form(rawdata, form, data)

                remote_addr = request.environ.get('REMOTE_ADDR', 'Uknown source')
                referer = request.environ.get('REFERER', '')
                lang = request.environ.get('HTTP_ACCEPT_LANGUAGE', '')
                agent = request.environ.get('HTTP_USER_AGENT', '')

                msg = BLOGPIT_COMMENT_MSG_TEMPLATE % (remote_addr, referer, remote_addr, lang, agent)

                ok = __blogpit.setarticle(path, newdata, msg)

                if ok:
                    flash(u'Thank you for your comment')
                else:
                    flash(u'Oops, we are unable to submit your comment at this \
                            time, please try again later!', 'error')

                return redirect(url_for('.blogpit_content', path=path))

            for field_name in form.errors:
                if form[field_name].flags.is_spamtrap:
                    spam_found = True

        else:
            form = None

        # Disable comment form for spammers
        if spam_found:
            spam_found = current_app.config.get('SPAM_MESSAGE','Comments are temporarily disabled, due to flying spamming monkeys' )
            form = None

        if request.is_xhr and current_app.config.get('SERVE_XHR_RAW', False):
            return current_app.response_class( get_article_raw(path), mimetype='text/plain', direct_passthrough=False)

        return render_template('blogpit/article.html',
                                        article=data, blogpit_path=path,
                                        form=form, spam_found=spam_found)

    return blogpit_blueprint


