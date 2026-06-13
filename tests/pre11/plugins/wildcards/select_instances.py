import pyblish.api


@pyblish.api.log
class CollectInstances(pyblish.api.Collector):
    hosts = ['*']
    version = (0, 0, 1)

    def process_context(self, context):
        files = context.create_instance(name='Files')
        files.append('Test1')
        files.append('Test2')
