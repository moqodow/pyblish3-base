"""Compatibility module"""

import inspect
from . import lib, logic
from .vendor import six

if six.PY2:
    get_arg_spec = inspect.getargspec
else:
    get_arg_spec = inspect.getfullargspec


@lib.deprecated
def process(func, plugins, context, test=None):
    r"""Primary processing logic

    Takes callables and data as input, and performs
    logical operations on them until the currently
    registered test fails.

    If `plugins` is a callable, it is called early, before
    processing begins. If `context` is a callable, it will
    be called once per plug-in.

    Arguments:
        func (callable): Callable taking three arguments;
             plugin(Plugin), context(Context) and optional
             instance(Instance). Each must provide a matching
             interface to their corresponding objects.
        plugins (list, callable): Plug-ins to process. If a
            callable is provided, the return value is used
            as plug-ins. It is called with no arguments.
        context (Context, callable): Context whose instances
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

    __plugins = plugins
    __context = context

    if test is None:
        test = logic.registered_test()

    if hasattr(__plugins, "__call__"):
        plugins = __plugins()

    def gen(plugin, instances):
        if plugin.__instanceEnabled__ and len(instances) > 0:
            for instance in instances:
                yield instance
        else:
            yield None

    vars = {
        "nextOrder": None,
        "ordersWithError": list()
    }

    # Clear introspection values
    # TODO(marcus): Return *next* pair, this currently
    #   returns the current pair.
    self = process
    self.next_plugin = None
    self.next_instance = None

    for Plugin in plugins:
        self.next_plugin = Plugin
        vars["nextOrder"] = Plugin.order

        if not test(**vars):
            if hasattr(__context, "__call__"):
                context = __context()

            args = get_arg_spec(Plugin.process).args

            # Backwards compatibility with `asset`
            if "asset" in args:
                args.append("instance")

            instances = logic.instances_by_plugin(context, Plugin)

            # Limit processing to plug-ins with an available instance
            if not instances and "*" not in Plugin.families:
                continue

            for instance in gen(Plugin, instances):
                if instance is None and "instance" in args:
                    continue

                # Provide introspection
                self.next_instance = instance

                try:
                    result = func(Plugin, context, instance)

                except Exception as exc:
                    # Any exception occuring within the function
                    # you pass is yielded, you are expected to
                    # handle it.
                    yield exc

                else:
                    # Make note of the order at which
                    # the potential error error occured.
                    if result["error"]:
                        if Plugin.order not in vars["ordersWithError"]:
                            vars["ordersWithError"].append(Plugin.order)
                    yield result

            # Clear current
            self.next_instance = None

        else:
            yield logic.TestFailed(test(**vars), vars)
            break


logic.process = process
