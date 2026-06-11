"""Mockup of potential integration with 3rd-party task managment suite"""

from unittest import mock

import pyblish.api

api = mock.MagicMock()


class IntegratInstancesFail(pyblish.api.Integrator):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        raise ValueError("Test fail")
