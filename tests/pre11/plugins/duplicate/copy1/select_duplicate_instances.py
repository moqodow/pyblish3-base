import pyblish.api


@pyblish.api.log
class CollectDuplicateInstance(pyblish.api.Collector):
    hosts = ['python']
    version = (0, 1, 0)
