# -*- coding: utf-8 -*-
from amplify.agent.objects.abstract import AbstractObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class Versions(object):
    def __init__(self, current=None, obsolete=None, old=None):
        self.current = current
        self.obsolete = obsolete
        self.old = old


class ObjectData(object):
    def __init__(self, object=None, config=None, filters=None):
        self.definition = object
        self.id = AbstractObject.hash(self.definition)
        self.type = self.definition.get('type')
        self.config = config if config else {}
        self.config['filters'] = filters or []


class CloudResponse(object):

    def __init__(self, response):
        """
        Init a CloudResponse object

        :param response: {} raw cloud response
        :return: CloudResponse
        """
        self.config = response.get('config', {})
        self.messages = response.get('messages', [])
        self.versions = Versions(**response.get('versions'))

        self.objects = []
        for raw_object_data in response.get('objects', []):
            self.objects.append(ObjectData(**raw_object_data))
