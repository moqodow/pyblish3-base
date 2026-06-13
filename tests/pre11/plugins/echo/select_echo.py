import pyblish.api


class CollectEcho(pyblish.api.Collector):
    hosts = ['*']
    version = (0, 0, 1)

    def process_context(self, context):
        print(context.data())
