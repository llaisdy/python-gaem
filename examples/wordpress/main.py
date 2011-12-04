import urlparse
import gaem
import gaem.http
import gaem.middleware
import gaem.middleware.api
import gaem.middleware.cache
import gaem.middleware.fetch
import gaem.middleware.dos
import gaem.utils.headers
import settings

class Sanitize(gaem.middleware.Base):
    """
    Normalize request and deny possible insecure requests.
    """

    def deny(self, request):
        return (request.path_qs.startswith('/wp-login.php')
                or request.path_qs.startswith('/wp-admin')
                or request.path_qs.startswith('/xmlrpc.php')
                or (not request.method in ('HEAD', 'GET')
                    and not 'x-gaem-api-key' in request.headers))

    def process_request(self, request):
        gaem.utils.headers.strip_cache(request.headers)
        if self.deny(request):
            return gaem.http.Response(body='403 Forbidden', status=403)
        return request

class Normalize(gaem.middleware.Base):
    """
    Rewrite URLs, clean headers and set expire times.
    """

    _strip_headers = ('server', 'x-pingback', 'x-powered-by')

    def __init__(self, url):
        self.url = url.rstrip('/')

    def process_response(self, response, request):
        """
        Rewrite URLS, make response acceptable to cache and set expire times.
        """
        gaem.utils.headers.strip(response.headers, self._strip_headers)
        gaem.utils.headers.strip_cookie(response.headers)
        # Get network locations (ex: "backend.example.org:8080")
        backend_url = urlparse.urlparse(self.url)
        request_url = urlparse.urlparse(request.url)
        # Rudimentary rewrite of backend to frontend URLs
        response.body = response.body.replace(backend_url.netloc,
                                              request_url.netloc)
        for name, value in response.headers.items():
            response.headers[name] = value.replace(backend_url.netloc,
                                                   request_url.netloc)
        # Define caching rules
        if response.status_int in (200, 301):
            if request_url.path.startswith('/wp-content/uploads/'):
                response.cache_expires(settings.EXPIRES_UPLOADS)
            elif (request_url.path == '/favicon.ico'
                  or request_url.path.startswith('/wp-content/')):
                response.cache_expires(settings.EXPIRES_STATIC)
            else:
                response.cache_expires(settings.EXPIRES_DEFAULT)
        return response

MIDDLEWARE_CLASSES = (
    Sanitize(),
    gaem.middleware.api.Cache(key=settings.KEY),
    gaem.middleware.cache.Memcache(),
    gaem.middleware.cache.Datastore(),
    gaem.middleware.dos.DoS(),
    Normalize(settings.URL),
    gaem.middleware.fetch.Fetch(url=settings.URL),
)

application = gaem.Application(MIDDLEWARE_CLASSES)

if __name__ == '__main__':
    application.run()
