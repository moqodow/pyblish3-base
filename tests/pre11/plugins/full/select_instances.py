
import pyblish.api


@pyblish.api.log
class CollectInstances(pyblish.api.Collector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        inst = context.create_instance(name='Test')
        inst.data['family'] =  'full'
        inst.data['selected'] =  True

        # The following will be set during
        # processing of other plugins
        inst.data['validated'] =  False
        inst.data['extracted'] =  False
        inst.data['conformed'] =  False
