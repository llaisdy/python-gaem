"""
Abstract component.
"""

class Base(object):
    """
    Abstract class which all components should inherit.
    """

    def process_request(self, request):
        return request

    def process_response(self, response, request):
        return response
