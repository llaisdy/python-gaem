"""
Component for handling API calls.
"""

from gaem import middleware

class Base(middleware.Base):
    """
    Base API component with method to validate request.
    """

    KEY_NAME = 'x-gaem-api-key'

    def __init__(self, key):
        self.key = key

    def valid(self, request):
        """
        Validate API request.
        """
        return self.key == request.headers.get(self.KEY_NAME)

class Cache(Base):

    def process_request(self, request):
        """
        Process cache clearing API calls.
        """
        if self.valid(request):
            api_meta = True
            fetch_meta = False
            # The caching components use this variable to decide if they
            # should clear their cache.
            if request.method == 'DELETE':
                request.meta['gaem.cache.clear'] = True
            else:
                api_meta = False
                fetch_meta = True
            request.meta['gaem.api'] = api_meta
            request.meta['gaem.fetch'] = fetch_meta
        return request
