"""
Django-like middleware for Google App Engine.
"""

from google.appengine.ext.webapp import util
from gaem import http

class Application(object):
    """
    wsgi application for handling a request and response.
    """

    def __init__(self, classes):
        self.classes = classes

    def __call__(self, environ, start_response):
        """
        Process a wsgi request through installed components and return the
        generated response.
        """
        count = 0
        response = None
        request = http.Request(environ)
        # Wind-up through each component calling process_request and using the
        # results to either start winding down up passing on up
        for cls in self.classes:
            value = cls.process_request(request)
            if isinstance(value, http.Response):
                response = value
                break
            else:
                request = value
            count += 1
        # If no component returned a response create a default 404 object
        if response is None:
            response = http.Response(body='404 Not Found', status=404)
            response.meta['gaem.response.default'] = True
        # Wind-down through the components calling process_response
        for cls in reversed(self.classes[0:count]):
            response = cls.process_response(response, request)
        # Return the wsgi response
        start_response(response.status, response.headers.items())
        return [response.body]

    def run(self):
        """
        Helper class for running the application
        """
        util.run_wsgi_app(self)
