# -*- coding: utf-8 -*-
import re

from amplify.agent.common.context import context
from amplify.agent.common.util.escape import prep_raw


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


REQUEST_RE = re.compile(r'(?P<request_method>[A-Z]+) (?P<request_uri>/.*) (?P<server_protocol>.+)')


class NginxAccessLogParser(object):
    """
    Nginx access log parser
    """
    combined_format = '$remote_addr - $remote_user [$time_local] "$request" ' + \
                      '$status $body_bytes_sent "$http_referer" "$http_user_agent"'

    default_variable = ['.+', str]

    common_variables = {
        'request': ['.+', str],
        'body_bytes_sent': ['\d+', int],
        'bytes_sent': ['\d+', int],
        'connection': ['[\d\s]+', str],
        'connection_requests': ['\d+', int],
        'msec': ['.+', float],
        'pipe': ['[p|\.]', str],
        'request_length': ['\d+', int],
        'request_time': ['.+', str],
        'status': ['\d+', str],
        'time_iso8601': ['.+', str],
        'time_local': ['.+', str],
        'upstream_response_time': ['.+', str],
        'upstream_response_length': ['.+', int],
        'upstream_connect_time': ['.+', str],
        'upstream_header_time': ['.+', str],
        'upstream_status': ['.+', str],
        'upstream_cache_status': ['.+', str],
        'gzip_ratio': ['.+', float],
    }

    # TODO: Remove this now semi-unnecessary variable.
    request_variables = {
        'request_method': ['[A-Z]+', str],
        'request_uri': ['/.*', str],
        'server_protocol': ['[\d\.]+', str],
    }

    comma_separated_keys = [
        'upstream_addr',
        'upstream_status'
    ]

    def __init__(self, raw_format=None):
        """
        Takes raw format and generates regex
        :param raw_format: raw log format
        """
        self.raw_format = self.combined_format if raw_format is None else raw_format

        self.keys = []
        self.regex_string = r''
        self.regex = None
        current_key = None

        # preprocess raw format and if we have trailing spaces in format we should remove them
        self.raw_format = prep_raw(self.raw_format).rstrip()

        def finalize_key():
            """
            Finalizes key:
            1) removes $ and {} from it
            2) adds a regex for the key to the regex_string
            """
            chars_to_remove = ['$', '{', '}']
            plain_key = current_key.translate(None, ''.join(chars_to_remove))

            self.keys.append(plain_key)
            rxp = self.common_variables.get(plain_key, self.default_variable)[0]

            # Handle formats with multiple instances of the same variable.
            var_count = self.keys.count(plain_key)
            if var_count > 1:  # Duplicate variables will be named starting at 2 (var, var2, var3, etc...)
                regex_var_name = '%s_occurance_%s' % (plain_key, var_count)
            else:
                regex_var_name = plain_key
            self.regex_string += '(?P<%s>%s)' % (regex_var_name, rxp)

        for char in self.raw_format:
            if current_key:
                if char.isalpha() or char.isdigit() or char == '_' or (char == '{' and current_key == '$'):
                    current_key += char
                elif char == '}':  # the end of ${key} format
                    current_key += char
                    finalize_key()
                else:  # finalize key and start a new one
                    finalize_key()

                    if char == '$':  # if there's a new key - create it
                        current_key = char
                    else:
                        # otherwise - add char to regex
                        current_key = None
                        if char.isalpha() or char.isdigit():
                            self.regex_string += char
                        else:
                            self.regex_string += '\%s' % char
            else:
                # if there's no current key
                if char == '$':
                    current_key = char
                else:
                    if char.isalpha() or char.isdigit():
                        self.regex_string += char
                    else:
                        self.regex_string += '\%s' % char

        # key can be the last one element in a string
        if current_key:
            finalize_key()

        self.regex = re.compile(self.regex_string)

    def parse(self, line):
        """
        Parses the line and if there are some special fields - parse them too
        For example we can get HTTP method and HTTP version from request

        :param line: log line
        :return: dict with parsed info
        """
        result = {'malformed': False}

        # parse the line
        common = self.regex.match(line)

        if common:
            for key in self.keys:
                # key local vars
                time_var = False

                func = self.common_variables[key][1] if key in self.common_variables \
                    else self.default_variable[1]
                try:
                    value = func(common.group(key))
                # for example gzip ratio can be '-' and float
                except ValueError:
                    value = 0

                # time variables should be parsed to array of float
                if key.endswith('_time'):
                    time_var = True
                    # skip empty vars
                    if value != '-':
                        array_value = []
                        for x in value.replace(' ', '').split(','):
                            x = float(x)
                            # workaround for an old nginx bug with time. ask lonerr@ for details
                            if x > 10000000:
                                continue
                            else:
                                array_value.append(x)
                        if array_value:
                            result[key] = array_value

                # Handle comma separated keys
                if key in self.comma_separated_keys:
                    if ',' in value:
                        list_value = value.replace(' ', '').split(',')  # remove spaces and split values into list
                        result[key] = list_value
                    else:
                        result[key] = [value]

                if key not in result and not time_var:
                    result[key] = value
        else:
            context.default_log.debug(
                'could not parse line "%s" with regex "%s"' % (
                    line, self.regex_string
                )
            )

        if 'request' in result:
            try:
                method, uri, proto = result['request'].split(' ')
            except:
                result['malformed'] = True

            if not result['malformed'] and len(method) < 3:
                result['malformed'] = True

            result['request_method'] = method
            result['request_uri'] = uri
            result['server_protocol'] = proto

        return result
