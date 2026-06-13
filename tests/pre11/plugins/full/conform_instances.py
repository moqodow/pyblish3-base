
import pyblish.api


@pyblish.api.log
class IntegratInstances(pyblish.api.Integrator):
    hosts = ['python']
    families = ['full']
    version = (0, 1, 0)

    def process_instance(self, instance):
        instance.data['integrated'] =  True
