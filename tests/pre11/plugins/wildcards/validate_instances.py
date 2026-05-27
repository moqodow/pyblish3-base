import pyblish.api


@pyblish.api.log
class ValidateInstances123(pyblish.api.Validator):
    hosts = ['*']
    families = ['*']
    version = (0, 0, 1)

    def process_instance(self, instance):
        raise ValueError("I was called")
