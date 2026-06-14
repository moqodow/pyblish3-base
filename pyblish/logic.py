"""Shared processing logic"""

import os
import sys
import logging
import traceback
import inspect

from . import _registered_test, lib
from .plugin import (
    Validator,

    # Matchin algorithms
    Intersection,
    Subset,
    Exact,

    registered_targets
)

_algorithms = {
    Intersection: lambda a, b: set(a).intersection(b),
    Subset: lambda a, b: set(a).issubset(b),
    Exact: lambda a, b: set(a) == set(b)
}

log = logging.getLogger("pyblish.logic")


class TestFailed(Exception):
    def __init__(self, msg, vars):
        super(TestFailed, self).__init__(msg)
        self.vars = vars


def default_test(**vars):
    r"""Evaluate whether or not to continue processing

    The test determines whether or not to proceed from one
    plug-in to the next. The `vars` are updated everytime
    a plug-in is about to be processed with information about
    the upcoming plug-in.

    Returning any value means failure, whereas 0, False and None
    represents success. Similar to return/exit codes. You can provide
    a message along with a failure, such as specifying why the test
    failed. The message can then be used by process handlers,
    such as a GUI.

    You can provide your own test by registering it, see example below.

    Contents of `vars`:
        nextOrder (int): Order of next plugin
        ordersWithError (list): Orders at which an error has occured

    """

    offset = 0.5
    validation_order = Validator.order

    # If validation is done
    if vars["nextOrder"] >= validation_order + offset:
        for order in vars["ordersWithError"]:
            if lib.inrange(order,
                           base=validation_order,
                           offset=offset):
                return "failed validation"


def register_test(test):
    """Register test used to determine when to abort processing

    Arguments:
        test (callable): Called with argument `vars` and returns
            either True or False. True means to continue,
            False to abort.

    Example:
        >>> # Register custom test
        >>> def my_test(**vars):
        ...   return 1
        ...
        >>> register_test(my_test)
        >>>
        >>> # Run test
        >>> if my_test(order=1, ordersWithError=[]):
        ...   print("Test passed")
        Test passed
        >>>
        >>> # Restore default
        >>> deregister_test()

    """

    _registered_test["default"] = test


def registered_test():
    """Return the currently registered test"""
    return _registered_test["default"]


def deregister_test():
    """Restore default test"""
    register_test(default_test)


def plugins_by_families(plugins, families):
    """Same as :func:`plugins_by_family` except it takes multiple families

    Arguments:
        plugins (list): List of plugins
        families (list): Families with which to compare against

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:

        if "*" in plugin.families:
            compatible.append(plugin)
            continue

        algorithm = _algorithms.get(plugin.match)

        assert algorithm, ("Plug-in did not provide "
                           "valid matching algorithm: %s" % plugin.match)

        if algorithm(plugin.families, families):
            compatible.append(plugin)

    return compatible


def plugins_by_family(plugins, family):
    """Convenience function to :func:`plugins_by_families`

    Arguments:
        plugins (list): List of plugins
        family (str): Family with which to compare against

    Returns:
        List of compatible plugins.

    """

    return plugins_by_families(plugins, [family])


def plugins_by_instance(plugins, instance):
    """Conveinence function for :func:`plugins_by_family`

    Arguments:
        plugins (list): Plug-ins to assess
        instance (Instance): Instance with which to compare against

    Returns:
        List of compatible plugins

    """

    family = instance.data.get("family")
    families = instance.data.get("families", [])

    return plugins_by_families(
        plugins, ([family] if family else []) + families)


def plugins_by_host(plugins, host):
    """Return compatible plugins `plugins` to host `host`

    Arguments:
        plugins (list): List of plugins
        host (str): Host with which compatible plugins are returned

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:
        # TODO(marcus): Expand to take partial wildcards e.g. "*Mesh"
        if any(x in getattr(plugin, "hosts", None) for x in (host, "*")):
            compatible.append(plugin)

    return compatible


def plugins_by_targets(plugins, targets):
    """Reutrn compatible plugins `plugins` to targets `targets`

    Arguments:
        plugins (list): List of plugins
        targets (list): List of targets with which to compare against

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:

        algorithm = _algorithms.get(plugin.match)

        assert algorithm, ("Plug-in did not provide "
                           "valid matching algorithm: %s" % plugin.match)

        if algorithm(plugin.targets, targets):
            compatible.append(plugin)

    return compatible


def instances_by_plugin(instances, plugin):
    """Return compatible instances `instances` to plugin `plugin`

    Return instances as they correspond to a plug-in, given
    an algorithm. The algorithm is determined by the `Plugin.match`

    When `match == Subset`, families of an instance must be a
    subset of families supported by a plug-in.

    Arguments:
        instances (list): List of instances
        plugin (Plugin): Plugin with which to compare against

    Returns:
        List of compatible instances

    Invariant:
        Order of remaining plug-ins must remain the same

    """

    algorithm = _algorithms.get(plugin.match)

    compatible = list()

    for instance in instances:

        if "*" in plugin.families:
            compatible.append(instance)
            continue

        assert algorithm, ("Plug-in did not provide "
                           "valid matching algorithm: %s" % plugin.match)

        family = instance.data.get("family")
        families = [family] if family else []
        families += instance.data.get("families", [])

        if algorithm(plugin.families, families):
            compatible.append(instance)

    return compatible


def _extract_traceback(exception):
    """Append traceback to `exception`

    This function safely extracts a traceback while being
    careful not to leak memory.

    Arguments:
        exception (Exception): Append traceback to here
            as "traceback" attribute.

    """

    exc_type = exc_value = exc_traceback = None

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except:
        pass

    finally:
        del(exc_type, exc_value, exc_traceback)


def Iterator(plugins, context, state=None, targets=None):
    """Primary iterator

    This is the brains of publishing. It handles logic related
    to which plug-in to process with which Instance or Context,
    in addition to stopping when necessary.

    Arguments:
        plugins (list): Plug-ins to consider
        context (list): Instances to consider
        state (dict): Mutable state
        targets (list, optional): Targets to include for publish session.

    """

    test = registered_test()
    state = state or {
        "nextOrder": None,
        "ordersWithError": set()
    }

    # Include "default" target and registered targets when no targets are
    # explicitly requested.
    if not targets:
        targets = ["default"] + registered_targets()

    plugins = plugins_by_targets(plugins, targets)

    for plugin in plugins:
        if not plugin.active:
            log.debug("%s was inactive, skipping.." % plugin)
            continue

        state["nextOrder"] = plugin.order

        message = test(**state)
        if message:
            log.error("Stopped due to %s" % message)
            return

        instances = instances_by_plugin(context, plugin)
        if plugin.__instanceEnabled__:
            for instance in instances:
                if instance.data.get("publish") is False:
                    log.debug("%s was inactive, skipping.." % instance)
                    continue

                yield plugin, instance

        else:
            yield plugin, None


def process(func, plugins, context, test=None):
    """Primary processing logic

    Takes data as input, and performs logical operations on 
    them until the currently registered test fails.

    Arguments:
        func (callable): Callable taking three arguments;
             plugin(Plugin), context(Context) and optional
             instance(Instance). Each must provide a matching
             interface to their corresponding objects.
        plugins (list): Plug-ins to process. If a
            callable is provided, the return value is used
            as plug-ins. It is called with no arguments.
        context (Context): Context whose instances
            are to be processed. If a callable is provided,
            the return value is used as context. It is called
            with no arguments.
        test (callable, optional): Provide custom test, defaults
            to the currently registered test.

    Yields:
        A result per complete process. If test fails,
        a TestFailed exception is returned, containing the
        variables used in the test. Finally, any exception
        thrown by `func` is yielded. Note that this is
        considered a bug in *your* code as you are the one
        supplying it.

    """
    
    test = test or registered_test()

    vars = {
        "nextOrder": None,
        "ordersWithError": list()
    }

    for plugin, instance in Iterator(plugins, context):
        vars["nextOrder"] = plugin.order
        args = inspect.getfullargspec(plugin.process).args
        instances = instances_by_plugin(context, plugin)

        # Limit processing to plug-ins with an available instance
        if not instances and "*" not in plugin.families:
            continue

        if instance is None and "instance" in args:
            continue

        if not test(**vars):
            try:
                result = func(plugin, context, instance)
            except Exception as exc:
                # Any exception occuring within the function
                # you pass is yielded, you are expected to
                # handle it.
                yield exc

            else:
                # Make note of the order at which
                # the potential error error occured.
                if result["error"]:
                    if plugin.order not in vars["ordersWithError"]:
                        vars["ordersWithError"].append(plugin.order)
                yield result
        else:
            yield TestFailed(test(**vars), vars)
            break
