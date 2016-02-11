# -*- coding: utf-8 -*-
import re

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) 2015, Nginx Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


error_re = {
    'http.request.buffered': [
        re.compile(r'.*client request body is buffered.*'),
    ],
    'upstream.response.buffered': [
        re.compile(r'.*upstream response is buffered.*'),
    ],
    'upstream.request.failed': [
        re.compile(r'.*failed.*while connecting to upstream, client.*'),
        re.compile(r'.*upstream timed out.*while connecting to upstream, client.*'),
        re.compile(r'.*upstream queue is full while connecting to upstream.*'),
        re.compile(r'.*no live upstreams while connecting to upstream, client.*'),
        re.compile(r'.*upstream connection is closed too while sending request to upstream, client.*'),
    ],
    'upstream.response.failed': [
        re.compile(r'.*failed.*while reading upstream.*'),
        re.compile(r'.*failed.*while reading response header from upstream, client.*'),
        re.compile(r'.*upstream timed out.*while reading response header from upstream, client.*'),
        re.compile(r'.*upstream buffer is too small to read response.*'),
        re.compile(r'.*upstream prematurely closed connection while reading response header from upstream, client.*'),
        re.compile(r'.*upstream sent no valid.*header while reading response.*'),
        re.compile(r'.*upstream sent invalid header.*'),
        re.compile(r'.*upstream sent invalid chunked response.*'),
        re.compile(r'.*upstream sent too big header while reading response header from upstream.*'),
    ]
}


class NginxErrorLogParser(object):
    """
    Nginx error log parser
    """

    short_name = 'nginx_elog'

    def parse(self, line):
        """
        Parses the line to find any kind of errors and return it once any first is found

        :param line: log line
        :return: str or None: error
        """
        for error, regexps in error_re.iteritems():
            for regexp in regexps:
                if re.match(regexp, line):
                    return error
        return None
