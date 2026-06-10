import os

from . import lib

import pyblish.api
import pyblish.util

from nose2.tools.decorators import (
    with_setup,
    with_teardown
)

def setup():
    lib.setup()
    pyblish.api.deregister_all_targets()


def teardown():
    pyblish.api.deregister_all_targets()
    lib.teardown()

def test_convenience_plugins_argument():
    """util._convenience() `plugins` argument works

    Issue: #286

    """

    count = {"#": 0}

    class PluginA(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            count["#"] += 1

    class PluginB(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            count["#"] += 10

    assert count["#"] == 0

    pyblish.api.register_plugin(PluginA)
    pyblish.util._convenience(plugins=[PluginB], order=0.5)

    assert count["#"] == 10, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_convenience_functions():
    """convenience functions works as expected"""

    count = {"#": 0}

    class Collector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            count["#"] += 1

    class Validator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    class Extractor(pyblish.api.InstancePlugin):
        order = pyblish.api.ExtractorOrder

        def process(self, instance):
            count["#"] += 100

    class Integrator(pyblish.api.ContextPlugin):
        order = pyblish.api.IntegratorOrder

        def process(self, instance):
            count["#"] += 1000

    class PostIntegrator(pyblish.api.ContextPlugin):
        order = pyblish.api.IntegratorOrder + 0.1

        def process(self, instance):
            count["#"] += 10000

    class NotCVEI(pyblish.api.ContextPlugin):
        """This plug-in is too far away from Integration to qualify as CVEI"""
        order = pyblish.api.IntegratorOrder + 2.0

        def process(self, instance):
            count["#"] += 100000

    assert count["#"] == 0

    for Plugin in (Collector,
                   Validator,
                   Extractor,
                   Integrator,
                   PostIntegrator,
                   NotCVEI):
        pyblish.api.register_plugin(Plugin)

    context = pyblish.util.collect()

    assert count["#"] == 1

    pyblish.util.validate(context)

    assert count["#"] == 11

    pyblish.util.extract(context)

    assert count["#"] == 111

    pyblish.util.integrate(context)

    assert count["#"] == 11111


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_multiple_instance_util_publish():
    """Multiple instances work with util.publish()

    This also ensures it operates correctly with an
    InstancePlugin collector.

    """

    count = {"#": 0}

    class MyContextCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("A")
            context.create_instance("B")
            count["#"] += 1

    class MyInstancePluginCollector(pyblish.api.InstancePlugin):
        order = pyblish.api.CollectorOrder + 0.1

        def process(self, instance):
            count["#"] += 1

    pyblish.api.register_plugin(MyContextCollector)
    pyblish.api.register_plugin(MyInstancePluginCollector)

    # Ensure it runs without errors
    pyblish.util.publish()

    assert count["#"] == 3


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_modify_context_during_CVEI():
    """Custom logic made possible via convenience members"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            camera = context.create_instance("MyCamera")
            model = context.create_instance("MyModel")

            camera.data["family"] = "camera"
            model.data["family"] = "model"

            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    pyblish.api.register_plugin(MyCollector)
    pyblish.api.register_plugin(MyValidator)

    context = pyblish.api.Context()

    assert count["#"] == 0, count

    pyblish.util.collect(context)

    assert count["#"] == 1, count

    context[:] = filter(lambda i: i.data["family"] == "camera", context)

    pyblish.util.validate(context)

    # Only model remains
    assert count["#"] == 11, count

    # No further processing occurs.
    pyblish.util.extract(context)
    pyblish.util.integrate(context)

    assert count["#"] == 11, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_environment_host_registration():
    """Host registration from PYBLISH_HOSTS works"""

    count = {"#": 0}
    hosts = ["test1", "test2"]

    # Test single hosts
    class SingleHostCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        host = hosts[0]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(SingleHostCollector)

    context = pyblish.api.Context()

    os.environ["PYBLISH_HOSTS"] = "test1"
    pyblish.util.collect(context)

    assert count["#"] == 1, count

    # Test multiple hosts
    pyblish.api.deregister_all_plugins()

    class MultipleHostsCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        host = hosts

        def process(self, context):
            count["#"] += 10

    pyblish.api.register_plugin(MultipleHostsCollector)

    context = pyblish.api.Context()

    os.environ["PYBLISH_HOSTS"] = os.pathsep.join(hosts)
    pyblish.util.collect(context)

    assert count["#"] == 11, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_publishing_explicit_targets():
    """Publishing with explicit targets works"""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(plugin)

    pyblish.util.publish(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(setup)
@with_teardown(teardown)
def test_publishing_explicit_targets_with_global():
    """Publishing with explicit and globally registered targets works"""

    count = {"#": 0}

    class Plugin1(pyblish.api.ContextPlugin):
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    class Plugin2(pyblish.api.ContextPlugin):
        targets = ["foo"]

        def process(self, context):
            count["#"] += 10

    pyblish.api.register_target("foo")
    pyblish.api.register_target("custom")
    pyblish.api.register_plugin(Plugin1)
    pyblish.api.register_plugin(Plugin2)

    pyblish.util.publish(targets=["custom"])

    assert count["#"] == 1, count
    assert pyblish.api.registered_targets() == ["foo", "custom"]

    pyblish.api.deregister_all_targets()


@with_setup(setup)
@with_teardown(teardown)
def test_per_session_targets():
    """Register targets per session works"""

    pyblish.util.publish(targets=["custom"])

    registered_targets = pyblish.api.registered_targets()
    assert registered_targets == [], registered_targets


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_publishing_collectors():
    """Running collectors with targets works"""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(plugin)

    pyblish.util.collect(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_publishing_validators():
    """Running validators with targets works"""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):
        order = pyblish.api.ValidatorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(plugin)

    pyblish.util.validate(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_publishing_extractors():
    """Running extractors with targets works"""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):
        order = pyblish.api.ExtractorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(plugin)

    pyblish.util.extract(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_publishing_integrators():
    """Running integrators with targets works"""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):
        order = pyblish.api.IntegratorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(plugin)

    pyblish.util.integrate(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_progress_existence():
    """Progress data member exists"""

    class plugin(pyblish.api.ContextPlugin):
        pass

    pyblish.api.register_plugin(plugin)

    result = next(pyblish.util.publish_iter())

    assert "progress" in result, result


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_publish_iter_increment_progress():
    """Publish iteration increments progress"""

    class pluginA(pyblish.api.ContextPlugin):
        pass

    class pluginB(pyblish.api.ContextPlugin):
        pass

    pyblish.api.register_plugin(pluginA)
    pyblish.api.register_plugin(pluginB)

    iterator = pyblish.util.publish_iter()

    pluginA_progress = next(iterator)["progress"]
    pluginB_progress = next(iterator)["progress"]

    assert pluginA_progress < pluginB_progress
