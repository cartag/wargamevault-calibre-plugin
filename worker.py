from __future__ import unicode_literals, division, absolute_import, print_function

__license__   = 'GPL v3'

import socket
import re
import datetime
import json
from threading import Thread

from calibre.ebooks.metadata.book.base import Metadata

import calibre_plugins.wargamevault.config as cfg

class Worker(Thread): # Get details

    '''
    Get book details from WarGameVault book page in a separate thread
    '''

    def __init__(self, url, result_queue, browser, log, relevance, plugin, timeout=20):
        Thread.__init__(self)
        self.daemon = True
        self.url, self.result_queue = url, result_queue
        self.log, self.timeout = log, timeout
        self.relevance, self.plugin = relevance, plugin
        self.browser = browser.clone_browser()
        self.cover_url = self.wargamevault_id = self.isbn = None

    def run(self):
        try:
            self.get_details()
        except:
            self.log.exception('get_details failed for url: %r'%self.url)

    def get_details(self):
        self.log.info('Starting the get_details method')
        try:
            self.log.info('WarGameVault product url: %r'%self.url)
            self.browser.set_handle_redirect(True)
            self.browser.set_debug_redirects(True)
            import logging
            logger = logging.getLogger("mechanize.http_redirects")
            logger.addHandler(self.log)
            logger.setLevel(logging.INFO)
            raw = self.browser.open_novisit(self.url, timeout=self.timeout).read().strip()
        except Exception as e:
            if callable(getattr(e, 'getcode', None)) and \
                    e.getcode() == 404:
                self.log.error('URL malformed: %r'%self.url)
                return
            attr = getattr(e, 'args', [None])
            attr = attr if attr else [None]
            if isinstance(attr[0], socket.timeout):
                msg = 'WarGameVault timed out. Try again later.'
                self.log.error(msg)
            else:
                msg = 'Failed to make details query: %r'%self.url
                self.log.exception(msg)
            return

        '''
        raw = raw.decode('utf-8', errors='replace')
        if '<title>404 - ' in raw:
            self.log.error('URL malformed: %r'%self.url)
            return
        '''

        try:
            data = json.loads(raw)
            #self.log.info(data)
        except:
            msg = 'Failed to parse WarGameVault product page: %r'%self.url
            self.log.exception(msg)
            return

        try:
            # Look at the Name attribute to make sure we were actually returned
            # the JSON for a book
            name = data['data']['attributes']['description']['name']
        except:
            msg = 'Failed to find WarGameVault product name in JSON data: %r'%self.url
            self.log.exception(msg)
            return

        self.parse_details(data)

    def parse_details(self, data):
        self.log.info('Started the parse_details process')

        try:
            wargamevault_id = self.parse_wargamevault_id(self.url)
            self.log.info('Parsed WarGameVault id of %r for url: %r'%(wargamevault_id,self.url))
        except:
            self.log.exception('Error parsing WarGameVault id for url: %r'%self.url)
            wargamevault_id = None

        try:
            title = self.parse_title(data)
        except:
            self.log.exception('Error parsing title for url: %r'%self.url)
            title = None

        try:
            authors = self.parse_authors(data)
        except:
            self.log.exception('Error parsing authors for url: %r'%self.url)
            authors = []

        if not title or not authors or not wargamevault_id:
            self.log.error('Could not find title/authors/wargamevault id for %r'%self.url)
            self.log.error('WarGameVault: %r Title: %r Authors: %r'%(wargamevault_id, title,
                authors))
            return

        mi = Metadata(title, authors)
        mi.set_identifier('wargamevault', wargamevault_id)
        self.wargamevault_id = wargamevault_id

        try:
            isbn = self.parse_isbn(data)
            if isbn:
                self.isbn = mi.isbn = isbn
        except:
            self.log.exception('Error parsing ISBN for url: %r'%self.url)

        try:
            mi.comments = self.parse_comments(data)
        except:
            self.log.exception('Error parsing comments for url: %r'%self.url)

        try:
            self.cover_url = self.parse_cover(data)
        except:
            self.log.exception('Error parsing cover for url: %r'%self.url)
        mi.has_cover = bool(self.cover_url)

        try:
            tags = self.parse_tags(data)
            if tags:
                mi.tags = tags
        except:
            self.log.exception('Error parsing tags for url: %r'%self.url)

        try:
            mi.pubdate = self.parse_publish_date(data)
        except:
            self.log.exception('Error parsing publish date for url: %r'%self.url)

        try:
            mi.publisher = self.parse_publisher(data)
        except:
            self.log.exception('Error parsing publisher for url: %r'%self.url)

        mi.source_relevance = self.relevance

        if self.wargamevault_id:
            if self.isbn:
                self.plugin.cache_isbn_to_identifier(self.isbn, self.wargamevault_id)
            if self.cover_url:
                self.plugin.cache_identifier_to_cover_url(self.wargamevault_id, self.cover_url)

        self.plugin.clean_downloaded_metadata(mi)

        self.log.info('Adding Metadata item to result_queue')
        self.result_queue.put(mi)

    def parse_wargamevault_id(self, url):
        return re.search(r'/products/(\d*)', url).groups(0)[0]

    def parse_title(self, data):
        title = data['data']['attributes']['description']['name']
        if not title:
            self.log("parse_title: no title found")
            return None
        self.log("parse_title: title=", title)
        return title.replace('>','').strip()

    def parse_authors(self, data):
        # WarGameVault has multiple contributor categories
        # which can be included as Authors depending on the user's preference.
        get_artists = cfg.plugin_prefs[cfg.STORE_NAME].get(cfg.KEY_GET_ARTISTS_AS_AUTHORS)
        get_editors = cfg.plugin_prefs[cfg.STORE_NAME].get(cfg.KEY_GET_EDITORS_AS_AUTHORS)
        get_contributors = cfg.plugin_prefs[cfg.STORE_NAME].get(cfg.KEY_GET_CONTRIBUTORS_AS_AUTHORS)
        authors = data['data']['attributes']['authors']
        if get_artists:
            authors += data['data']['attributes']['artists']
        if get_editors:
            authors += data['data']['attributes']['editors']
        if get_contributors:
            authors += data['data']['attributes']['contributors']

        if len(authors) == 0:
            authors = ['Unknown']

        self.log("parse_authors: authors=", authors)
        return authors

    def parse_comments(self, data):
        comments = data['data']['attributes']['description']['description']
        #self.log('parse_comments: comments=', comments)
        if comments:
            return comments

    def parse_cover(self, data):
        img_url = ('https://d1vzi28wh99zvq.cloudfront.net/images/' +
            data['data']['attributes']['image'])
        self.log('parse_cover: img_url=', img_url)
        if img_url:
            return img_url

    def parse_isbn(self, data):
        isbn = data['data']['attributes']['isbn']
        self.log('parse_isbn: isbn=', isbn)
        if isbn:
            return isbn

    def parse_publish_date(self, data):
        pub_date = data['data']['attributes']['dateCreated']
        self.log('parse_publish_date: pub_date=', pub_date)
        if pub_date:
            return datetime.datetime.fromisoformat(pub_date)

    def parse_publisher(self, data):
        for include in data['included']:
            if include['type'] == 'Publisher':
                publisher = include['attributes']['name']
                self.log('parse_publisher: publisher=', publisher)
                return publisher

    def parse_tags(self, data):
        # WarGameVault has multiple optional sections which can be used as tags depending on the user's preference.
        calibre_tags = []
        get_category = cfg.plugin_prefs[cfg.STORE_NAME].get(cfg.KEY_GET_CATEGORY_AS_TAGS)
        get_filter = cfg.plugin_prefs[cfg.STORE_NAME].get(cfg.KEY_GET_FILTER_AS_TAGS)
        for include in data['included']:
            if (get_category and include['type'] == 'Category') or (get_filter and include['type'] == 'Filter'):
                calibre_tags.append((include['attributes']['descriptions'][0]['name']).replace("&#039;","'"))

        self.log('parse_tags: calibre_tags=', calibre_tags)
        if len(calibre_tags) > 0:
            return calibre_tags
