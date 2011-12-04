"""
Helper functions for cleaning headers.
"""

COOKIE_HEADERS = ('cookie', 'set-cookie')

CACHE_HEADERS = ('cache-control', 'etag', 'expires', 'if-modified-since',
                 'if-none-match', 'pragma', 'last-modified') + COOKIE_HEADERS

def strip(headers, to_strip):
    for name in to_strip:
        if name in headers:
            del headers[name]

def strip_cache(headers):
    strip(headers, CACHE_HEADERS)

def strip_cookie(headers):
    strip(headers, COOKIE_HEADERS)
