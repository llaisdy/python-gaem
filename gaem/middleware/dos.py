"""
A basic component to prevent denial-of-service attacks against the backend
server.
"""

from google.appengine.api import memcache
from gaem import http
from gaem import middleware

class DoS(middleware.Base):
    """
    Component uses requester IP address to track requests and will deny a
    request if a requester exceeds a predefined threshold.
    """

    def __init__(self, timeout=30, count=60, key_prefix='default'):
        self.timeout = timeout
        self.count = count
        self.key_prefix = key_prefix

    def key(self, request):
        return '.'.join(['gaem', 'protection', 'dos', self.key_prefix,
                         request.remote_addr])

    def send_response(self, request):
        return http.Response(body='503 Service Unavailable', status=504)

    def process_request(self, request):
        key = self.key(request)
        count = memcache.incr(key)
        if count is None:
            # Handle possible race condition
            if not memcache.add(key, 1, time=self.timeout):
                count = memcache.incr(key)
        # memcache service is probably down
        if count is None:
            count = 1
        if count >= self.count:
            return self.send_response(request)
        return request
