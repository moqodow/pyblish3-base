"""Plugins for testing purposes.

Source them like this from within a test function:

pyblish.api.deregister_all_paths()
pyblish.api.register_plugin_path(os.path.dirname(__file__))

This ensures that the plugins are actually loaded through `plugin.discover`.
"""
import pyblish.api


class FailingExplicitPlugin(pyblish.api.InstancePlugin):
    """Raise an exception."""

    def process(self, instance):
        raise Exception("A test exception")


class FailingImplicitPlugin(pyblish.api.Validator):
    """Raise an exception."""

    def process(self, instance):
        raise Exception("A test exception")
