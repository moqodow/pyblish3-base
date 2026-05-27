import pyblish.api


@pyblish.api.log
class SelectInstances(pyblish.api.Selector):
    hosts = ['*']
    version = (0, 0, 1)

    def process_context(self, context):
        files = context.create_instance(name='Files')
        files.add('Test1')
        files.add('Test2')
