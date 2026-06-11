"""This plugin is incomplete and can't be used"""

import pyblish.api


@pyblish.api.log
class CollectMissingHosts(pyblish.api.Collector):
    """Collect instances"""

    requires = False
    version = "Invalid"
