from __future__ import unicode_literals, division, absolute_import, print_function

__license__   = 'GPL v3'

import time
import re
import json
try:
    from urllib import parse
except ImportError:
    import urllib
try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue

from calibre import as_unicode
from calibre.ebooks.metadata.sources.base import Source

class DriveThruRPG(Source):

    name                    = 'DriveThruRPG'
    description             = 'Downloads metadata from drivethrurpg.com'
    author                  = 'quickwick'
    version                 = (1, 0, 0)
    minimum_calibre_version = (8, 6, 0)

    ID_NAME = 'drivethrurpg'
    capabilities = frozenset(['identify', 'cover'])
    touched_fields = frozenset(['title', 'authors', 'identifier:drivethrurpg',
        'comments', 'publisher', 'pubdate', 'tags', 'series'])
    has_html_comments = True
    supports_gzip_transfer_encoding = True

    BASE_URL = 'https://www.drivethrurpg.com'
    BASE_API_URL = 'https://api.drivethrurpg.com/api/vBeta'

    # This method is expected for a metadata source plugin
    def config_widget(self):
        '''
        Overriding the default configuration screen for our own custom configuration
        '''
        from calibre_plugins.drivethrurpg.config import ConfigWidget
        return ConfigWidget(self)

    # This method is expected for a metadata source plugin
    def get_book_url(self, identifiers):
        drivethrurpg_id = identifiers.get(self.ID_NAME, None)
        if drivethrurpg_id:
            return (self.ID_NAME, drivethrurpg_id,
                    '%s/product/%s'%(self.BASE_URL, drivethrurpg_id))

    # This method is custom to this plugin
    def get_book_dl_url(self, identifiers):
        drivethrurpg_id = identifiers.get(self.ID_NAME, None)
        if drivethrurpg_id:
            return (self.ID_NAME, drivethrurpg_id,
                    '%s/products/%s'%(self.BASE_API_URL, drivethrurpg_id))

    # This method is expected for a metadata source plugin
    def id_from_url(self, url):
        match = re.match(r'/products/(\d*)', url)
        if match:
            return (self.ID_NAME, match.groups(0)[0])
        return None

    # This method is expected for a metadata source plugin
    def get_cached_cover_url(self, identifiers):
        url = None
        drivethrurpg_id = identifiers.get(self.ID_NAME, None)
        if drivethrurpg_id is None:
            isbn = identifiers.get('isbn', None)
            if isbn is not None:
                drivethrurpg_id = self.cached_isbn_to_identifier(isbn)
        if drivethrurpg_id is not None:
            url = self.cached_identifier_to_cover_url(drivethrurpg_id)

        return url

    # This method is expected for a metadata source plugin
    def identify(self, log, result_queue, abort, title=None, authors=None,
            identifiers={}, timeout=30):
        log.info('Started the identify method')
        '''
        Note this method will retry without identifiers automatically if no
        match is found with identifiers.
        '''
        matches = []
        # Unlike the other metadata sources, if we have a DriveThruRPG id then we
        # do not need to fire a "search" at DriveThruRPG.com. Instead we will be
        # able to go straight to the URL for that book.
        drivethrurpg_id = identifiers.get(self.ID_NAME, None)

        br = self.browser

        if drivethrurpg_id:
            log.info('Found a DriveThruRPG id of %s'%drivethrurpg_id)
            matches.append(self.get_book_dl_url(identifiers)[2])
        else:
            # Search DriveThruRPG using the title
            title_tokens = list(self.get_title_tokens(title,
                                strip_joiners=True, strip_subtitle=True))
            title_text = ' '.join(title_tokens)
            log.info('Constructed a title_text string of %s'%title_text)

            query_params = parse.urlencode({'page':1,'pageSize':6,'groupId':1,'name':title_text,'order[matchWeight]':'desc',
                                      'siteId':10,'contentRating[lte]':1,'status':1,'partial':'false'},quote_via=parse.quote)
            #log.info('Constructed a urlencoded query_params string of %s'%query_params)
            query_url = DriveThruRPG.BASE_API_URL + '/products?' + query_params

            if query_params is None:
                log.error('Insufficient metadata to construct query')
                return
            try:
                log.info('Querying: %s'%query_url)
                br.set_handle_redirect(True)
                br.set_debug_redirects(True)
                # Perform a product search on DriveThruRPG
                response = br.open_novisit(query_url, timeout=timeout)
                #log.info('Received search response of : %s'%response)
            except Exception as e:
                log.exception(e)
                err = 'Failed to make identify query: %s'%(query_url)
                log.exception(err)
                return as_unicode(e)

            # Get all the individual product URLs from the search response
            try:
                raw = response.read().strip()
                if not raw:
                    log.error('Failed to get raw result for query: %s'%(query_url))
                    return
                data = json.loads(raw)
                for product in data['data']:
                    product_url = DriveThruRPG.BASE_API_URL + '/products/' + str(product['attributes']['productId'])
                    log.info('Identified product URL in search results: %s'%product_url)
                    matches.append(product_url)
            except:
                msg = 'Failed to parse DriveThruRPG page for query: %s'%(query_url)
                log.exception(msg)
                return msg

        if abort.is_set():
            return

        log.info('Found %r matches in the query results'%(len(matches)))
        #log.info('Matches: %r'%matches)

        from calibre_plugins.drivethrurpg.worker import Worker
        workers = [Worker(url, result_queue, br, log, i, self) for i, url in
                enumerate(matches)]

        for w in workers:
            w.start()
            # Don't send all requests at the same time
            time.sleep(0.1)

        while not abort.is_set():
            a_worker_is_alive = False
            for w in workers:
                w.join(0.2)
                if abort.is_set():
                    break
                if w.is_alive():
                    a_worker_is_alive = True
            if not a_worker_is_alive:
                break

        return None

    # This method is expected for a metadata source plugin
    def download_cover(self, log, result_queue, abort,
            title=None, authors=None, identifiers={}, timeout=30):
        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url is None:
            log.info('No cached cover found, running identify')
            rq = Queue()
            self.identify(log, rq, abort, title=title, authors=authors,
                    identifiers=identifiers)
            if abort.is_set():
                return
            results = []
            while True:
                try:
                    results.append(rq.get_nowait())
                except Empty:
                    break
            results.sort(key=self.identify_results_keygen(
                title=title, authors=authors, identifiers=identifiers))
            for mi in results:
                cached_url = self.get_cached_cover_url(mi.identifiers)
                if cached_url is not None:
                    break
        if cached_url is None:
            log.info('No cover found')
            return

        if abort.is_set():
            return
        br = self.browser
        log('Downloading cover from:', cached_url)
        try:
            cdata = br.open_novisit(cached_url, timeout=timeout).read()
            result_queue.put((self, cdata))
        except:
            log.exception('Failed to download cover from:', cached_url)

if __name__ == '__main__': # tests
    # To run these test use:
    # calibre-debug -e __init__.py
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
            title_test, authors_test)
    test_identify_plugin(DriveThruRPG.name,
        [

            ( # A book with a DriveThruRPG id
                {'identifiers':{'drivethrurpg': '457226'}},
                    #'title':'Shadow of the Weird Wizard', 'authors':['Robert J Schwalb']},
                [title_test('Shadow of the Weird Wizard',
                    exact=True), authors_test(['Robert J Schwalb'])]

            ),

            ( # A book with no id specified
                {'title':"Secrets of the Weird Wizard", 'authors':['Robert J. Schwalb']},
                [title_test("Secrets of the Weird Wizard",
                    exact=True), authors_test(['Robert J. Schwalb'])]

            ),

        ])
