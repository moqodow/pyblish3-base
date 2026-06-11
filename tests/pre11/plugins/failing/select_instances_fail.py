
import pyblish.api


@pyblish.api.log
class CollectInstancesError(pyblish.api.Collector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        raise ValueError("Test exception")
