"""
A collection of caching components.
"""

from datetime import datetime
from google.appengine.api import memcache
from google.appengine.ext import db
from gaem import http
from gaem import middleware
from gaem import utils
from gaem.utils import cache

class Base(middleware.Base):
    """
    An abstract class for creating caching compontents.

    A new cache compontent should only have to implement the get, set and
    delete methods.
    """

    def __init__(self, default_max_age=120):
        self.default_max_age = default_max_age

    def key(self, request):
        """
        A unique key which can be used for persisting response objects.
        """
        return '.'.join(['gaem', 'cache', request.path_qs])

    @staticmethod
    def is_cacheable(obj):
        """
        Check if a Request or Response object is cacheable.
        """
        if isinstance(obj, http.Response):
            return (not 'set-cookie' in obj.headers
                and not obj.cache_control.no_cache
                and not obj.cache_control.no_store
                and not obj.cache_control.must_revalidate
                and not obj.cache_control.proxy_revalidate
                and (obj.cache_control.max_age is None
                     or obj.cache_control.max_age > 0)
                and obj.status_int in (200, 301))
        else:
            return (obj.method in ('GET', 'HEAD')
                and not 'cookie' in obj.headers
                and not obj.cache_control.no_cache
                and not obj.cache_control.no_store
                and (obj.cache_control.max_age is None
                     or obj.cache_control.max_age > 0))

    def expire(self, request):
        """
        Expire response from cache.
        """
        raise NotImplementedError

    def get(self, request):
        """
        Retrieve response from cache.
        """
        raise NotImplementedError

    def set(self, response, request):
        """
        Persist response in cache.
        """
        raise NotImplementedError

    def process_request(self, request):
        """
        Handle generic request logic.
        """
        # Transform HEAD into GET so we can store the full request and just
        # respond with the headers.
        if request.method == 'HEAD':
            request.meta['gaem.cache.request.method'] = request.method
            request.method = 'GET'
        # Clear or retrieve response
        if request.meta.get('gaem.cache.clear'):
            self.expire(request)
        elif self.is_cacheable(request):
            return self.get(request)
        return request

    def process_response(self, response, request):
        """
        Handle generic response logic.
        """
        if not request.meta.get('gaem.api'):
            # Used to transform a GET into a HEAD if modified by process_request
            if 'gaem.cache.request.method' in request.meta:
                request.method = request.meta['gaem.cache.request.method']
            # A graceful way to serve an expired response from cache if we
            # can't get something better.
            if (response.meta.get('gaem.response.default')
                and request.meta.get('gaem.cache.response')):
                response = request.meta['gaem.cache.response']
                del request.meta['gaem.cache.response']
                response.meta['gaem.response.graceful'] = True
                response.cache_control.max_age = self.default_max_age
            # If cacheable persist response
            if self.is_cacheable(response):
                self.set(response, request)
        return response

class Memcache(Base):
    """
    Google memcache service implementation of cache compontent.
    """

    def expire(self, request):
        """
        Remove response from memcache if expired.
        """
        memcache.delete(self.key(request))

    def get(self, request):
        """
        Retrieve response from memcache.
        """
        data = memcache.get(self.key(request))
        if not data is None:
            response = http.Response(status=int(data.get('status', 200)),
                                     headerlist=data.get('headers', []))
            if request.method != 'HEAD':
                response.body = data.get('body', '')
            return response
        return request

    def set(self, response, request):
        """
        Persist response to memcache.
        """
        memcache.set(self.key(request), {
            'body': response.body,
            'status': response.status_int,
            'headers': response.headers.items(),
        }, time=self.default_max_age if response.cache_control.max_age is None
                                     else response.cache_control.max_age)

class CacheObject(db.Expando):
    """
    Model used to persist response objects to the datastore.
    """
    body = db.BlobProperty()
    status = db.IntegerProperty()
    headers = db.StringListProperty()
    expires = db.DateTimeProperty()

    def is_expired(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        return timestamp > self.expires

    def get_max_age(self):
        return cache.create_max_age(self.expires)

    def set_max_age(self, seconds):
        self.expires = cache.create_expires(seconds)

class Datastore(Base):
    """
    Google datastore implementation of cache compontent.
    """

    def expire(self, request, data=None):
        """
        Expire datastore persisted response object.

        We don't actually delete the object so we can gracefully fallback
        if the backend is down.
        """
        if data is None:
            data = CacheObject.get_by_key_name(self.key(request))
        if not data is None:
            data.expires = datetime.now()
            data.put()
        return data

    def get(self, request):
        """
        Retrieve response object from datastore.
        """
        data = CacheObject.get_by_key_name(self.key(request))
        if not data is None:
            response = http.Response(
                status=int(data.status),
                headerlist=utils.list_to_headerdict(data.headers).items()
            )
            if request.method != 'HEAD':
                response.body = data.body
            if not data.is_expired:
                return response
            # Save response object so we can gracefully fallback if needed
            if not 'gaem.cache.response' in request.meta:
                request.meta['gaem.cache.response'] = response
        return request

    def set(self, response, request):
        """
        Persist response to datastore.
        """
        data = CacheObject.get_by_key_name(self.key(request))
        if data is None:
            data = CacheObject(key_name=self.key(request))
        data.body = response.body
        data.status = response.status_int
        data.set_max_age(self.default_max_age if response.cache_control.max_age \
                         is None else response.cache_control.max_age)
        data.headers = utils.headerdict_to_list(response.headers)
        data.put()
