import os
import contextlib

# Local library
from . import lib

import pyblish.api
import pyblish.logic
import pyblish.plugin
import pyblish.util

from nose2.tools.decorators import (
    with_setup,
    with_teardown
)


@contextlib.contextmanager
def no_guis():
    os.environ.pop("PYBLISHGUI", None)
    for gui in pyblish.logic.registered_guis():
        pyblish.logic.deregister_gui(gui)

    yield


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_iterator():
    """Iterator skips inactive plug-ins and instances"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            inactive = context.create_instance("Inactive")
            active = context.create_instance("Active")

            inactive.data["publish"] = False
            active.data["publish"] = True

            count["#"] += 1

    class MyValidatorA(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        active = False

        def process(self, instance):
            count["#"] += 10

    class MyValidatorB(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 100

    context = pyblish.api.Context()
    plugins = [MyCollector, MyValidatorA, MyValidatorB]

    assert count["#"] == 0, count

    for Plugin, instance in pyblish.logic.Iterator(plugins, context):
        assert instance.name != "Inactive" if instance else True
        assert Plugin.__name__ != "MyValidatorA"

        pyblish.plugin.process(Plugin, context, instance)

    # Collector runs once, one Validator runs once
    assert count["#"] == 101, count


def test_iterator_with_explicit_targets():
    """Iterator skips non-targeted plug-ins"""

    count = {"#": 0}

    class MyCollectorA(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        targets = ["studio"]

        def process(self, context):
            count["#"] += 1

    class MyCollectorB(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            count["#"] += 10

    class MyCollectorC(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        targets = ["studio"]

        def process(self, context):
            count["#"] += 100

    context = pyblish.api.Context()
    plugins = [MyCollectorA, MyCollectorB, MyCollectorC]

    assert count["#"] == 0, count

    for Plugin, instance in pyblish.logic.Iterator(
        plugins, context, targets=["studio"]
    ):
        assert Plugin.__name__ != "MyCollectorB"

        pyblish.plugin.process(Plugin, context, instance)

    # Collector runs once, one Validator runs once
    assert count["#"] == 101, count


def test_register_gui():
    """Registering at run-time takes precedence over those from environment"""

    with no_guis():
        os.environ["PYBLISHGUI"] = "second,third"
        pyblish.logic.register_gui("first")

        print(pyblish.logic.registered_guis())
        assert pyblish.logic.registered_guis() == ["first", "second", "third"]

    with no_guis():
        os.environ["PYBLISH_GUI"] = "second,third"
        pyblish.logic.register_gui("first")

        print(pyblish.logic.registered_guis())
        assert pyblish.logic.registered_guis() == ["first", "second", "third"]


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_subset_match():
    """Plugin.match = pyblish.api.Subset works as expected"""

    count = {"#": 0}

    class MyPlugin(pyblish.api.InstancePlugin):
        families = ["a", "b"]
        match = pyblish.api.Subset

        def process(self, instance):
            count["#"] += 1

    context = pyblish.api.Context()

    context.create_instance("not_included_1", families=["a"])
    context.create_instance("not_included_1", families=["x"])
    context.create_instance("included_1", families=["a", "b"])
    context.create_instance("included_2", families=["a", "b", "c"])

    pyblish.util.publish(context, plugins=[MyPlugin])

    assert count["#"] == 2

    instances = pyblish.logic.instances_by_plugin(context, MyPlugin)
    assert list(i.name for i in instances) == ["included_1", "included_2"]


def test_subset_exact():
    """Plugin.match = pyblish.api.Exact works as expected"""

    count = {"#": 0}

    class MyPlugin(pyblish.api.InstancePlugin):
        families = ["a", "b"]
        match = pyblish.api.Exact

        def process(self, instance):
            count["#"] += 1

    context = pyblish.api.Context()

    context.create_instance("not_included_1", families=["a"])
    context.create_instance("not_included_1", families=["x"])
    context.create_instance("not_included_3", families=["a", "b", "c"])
    instance = context.create_instance("included_1", families=["a", "b"])

    # Discard the solo-family member, which defaults to `default`.
    #
    # When using multiple families, it is common not to bother modifying
    # `family`, and in the future this member needn't be there at all and
    # may/should be removed. But till then, for complete clarity, it might
    # be worth removing this explicitly during the creation of instances
    # if instead choosing to use the `families` key.
    instance.data.pop("family")

    pyblish.util.publish(context, plugins=[MyPlugin])

    assert count["#"] == 1

    instances = pyblish.logic.instances_by_plugin(context, MyPlugin)
    assert list(i.name for i in instances) == ["included_1"]


def test_plugins_by_families():
    """The right plug-ins are returned from plugins_by_families"""

    class ClassA(pyblish.api.Collector):
        families = ["a"]

    class ClassB(pyblish.api.Collector):
        families = ["b"]

    class ClassC(pyblish.api.Collector):
        families = ["c"]

    class ClassD(pyblish.api.Collector):
        families = ["a", "b"]
        match = pyblish.api.Intersection

    class ClassE(pyblish.api.Collector):
        families = ["a", "b"]
        match = pyblish.api.Subset

    class ClassF(pyblish.api.Collector):
        families = ["a", "b"]
        match = pyblish.api.Exact

    assert pyblish.logic.plugins_by_families(
        [ClassA, ClassB, ClassC], ["a", "z"]) == [ClassA]

    assert pyblish.logic.plugins_by_families(
        [ClassD, ClassE, ClassF], ["a"]) == [ClassD]

    assert pyblish.logic.plugins_by_families(
        [ClassD, ClassE, ClassF], ["a", "b"]) == [ClassD, ClassE, ClassF]

    assert pyblish.logic.plugins_by_families(
        [ClassD, ClassE, ClassF], ["a", "b", "c"]) == [ClassD, ClassE]


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_extracted_traceback_contains_correct_backtrace():
    pyblish.api.register_plugin_path(os.path.dirname(__file__))

    context = pyblish.api.Context()
    context.create_instance('test instance')

    plugins = pyblish.api.discover()
    plugins = [p for p in plugins if p.__name__ in
               ('FailingExplicitPlugin', 'FailingImplicitPlugin')]
    pyblish.util.publish(context, plugins)

    for result in context.data['results']:
        assert result["error"].traceback[0] == plugins[0].__module__
        formatted_tb = result['error'].formatted_traceback
        assert formatted_tb.startswith('Traceback (most recent call last):\n')
        assert formatted_tb.endswith('\nException: A test exception\n')
        assert 'File "{0}",'.format(plugins[0].__module__) in formatted_tb
