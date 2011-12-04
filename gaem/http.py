"""
Base HTTP Request and Response objects.
"""

import webob

class Base(object):

    @property
    def meta(self):
        """
        A standardized location for passing data between components.
        """
        if not hasattr(self, '_meta'):
            self._meta = {}
        return self._meta

class Response(webob.Response, Base):
    """
    The HTTP response object.
    """

class Request(webob.Request, Base):
    """
    The HTTP request object.
    """
