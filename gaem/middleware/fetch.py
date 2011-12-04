"""
Proxy request objects to backend servers.
"""

import copy
import logging
from google.appengine.api import urlfetch
from gaem import http
from gaem import middleware
from gaem.utils import headers

class Fetch(middleware.Base):
    """
    Uses Google urlfetch service to retrieve a response from a predefined URL.
    """

    _fetch_method = {
        'DELETE': urlfetch.DELETE,
        'GET': urlfetch.GET,
        'HEAD': urlfetch.HEAD,
        'POST': urlfetch.POST,
        'PUT': urlfetch.PUT,
    }
    _strip_headers = ('content-length', 'host', 'vary', 'via', 'x-forwarded-for')

    def __init__(self, url, follow_redirects=False, deadline=10):
        self.url = url
        self.follow_redirects = follow_redirects
        self.deadline = deadline

    def process_request(self, request):
        """
        Request and return response from backend server(s).
        """
        if request.meta.get('gaem.fetch') is False:
            return request
        url = self.url.rstrip('/')
        fetch_headers = copy.copy(request.headers)
        headers.strip_cache(fetch_headers)
        headers.strip(fetch_headers, self._strip_headers)
        # Revalidate (GAE uses a proxy for urlfetch)
        fetch_headers['Cache-Control'] = 'no-cache'
        try:
            fetched = urlfetch.fetch(url=url+request.path_qs,
                                     payload=request.body,
                                     method=self._fetch_method[request.method],
                                     headers=fetch_headers,
                                     allow_truncated=True,
                                     follow_redirects=self.follow_redirects,
                                     deadline=self.deadline)
            return http.Response(body=fetched.content,
                                 status=int(fetched.status_code),
                                 headerlist=fetched.headers.items())
        except urlfetch.Error, error:
            logging.error('gaem.middleware.fetch: %r' % error)
            return request
