# -*- coding: utf-8 -*-
from collections import namedtuple


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov",
    "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen",
    "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


INET_IPV4 = namedtuple('INET_IPV4', ('host', 'port'))
