"""
Misc helper functions.
"""

import datetime
import time
from webob import headerdict

def epoch(dt=None):
    if dt is None:
        dt = datetime.datetime.now()
    return int(time.mktime(dt.timetuple()))

def pair(iterable_list):
    iterable = iter(iterable_list)
    while True:
        yield(iterable.next(), iterable.next())

def headerdict_to_list(header_dict):
    header_list = []
    for name, value in header_dict.items():
        header_list.append(name)
        header_list.append(value)
    return header_list

def list_to_headerdict(header_list):
    header_list = list(pair(header_list))
    header_dict = headerdict.HeaderDict()
    for values in header_list:
        header_dict.add(*values)
    return header_dict
