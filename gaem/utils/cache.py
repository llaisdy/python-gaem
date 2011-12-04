"""
Helper functions for expire times.
"""

from datetime import datetime
from datetime import timedelta

def create_max_age(expires, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    delta = timestamp - expires
    return expires.days * 86400 + expires.seconds

def create_expires(seconds, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp + timedelta(seconds=seconds)
