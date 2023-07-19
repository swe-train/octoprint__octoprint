"""
This module represents OctoPrint's plugin subsystem. This includes management and helper methods as well as the
registered plugin types.
"""

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"

import logging
import os

from octoprint.plugin.core import Plugin, PluginInfo, PluginManager  # noqa: F401
from octoprint.plugin.types import *  # noqa: F401,F403 ## used by multiple other modules
from octoprint.plugin.types import OctoPrintPlugin, SettingsPlugin
from octoprint.settings import settings as s
from octoprint.util import deprecated

# singleton
_instance = None


def _validate_plugin(phase, plugin_info):
    return True


def plugin_manager(
    init=False,
    plugin_folders=None,
    plugin_bases=None,
    plugin_entry_points=None,
    plugin_disabled_list=None,
    plugin_sorting_order=None,
    plugin_blacklist=None,
    plugin_restart_needing_hooks=None,
    plugin_obsolete_hooks=None,
    plugin_considered_bundled=None,
    plugin_validators=None,
    compatibility_ignored_list=None,
):
    """
    Factory method for initially constructing and consecutively retrieving the [PluginManager][octoprint.plugin.core.PluginManager]
    singleton.

    Will set the logging prefix to `octoprint.plugins.`.

    Arguments:
        init (bool): A flag indicating whether this is the initial call to construct the singleton (`True`) or not
            (`False`, default). If this is set to `True` and the plugin manager has already been initialized, a [ValueError][]
            will be raised. The same will happen if the plugin manager has not yet been initialized and this is set to
            False.
        plugin_folders (list): A list of folders (as strings containing the absolute path to them) in which to look for
            potential plugin modules. If not provided this defaults to the configured `plugins` base folder and
            `src/plugins` within OctoPrint's code base.
        plugin_bases (list): A list of recognized plugin base classes for which to look for provided implementations. If not
            provided this defaults to `octoprint.plugin.types.OctoPrintPlugin`.
        plugin_entry_points (list): A list of entry points pointing to modules which to load as plugins. If not provided
            this defaults to the entry point `octoprint.plugin`.
        plugin_disabled_list (list): A list of plugin identifiers that are currently disabled. If not provided this
            defaults to all plugins for which `enabled` is set to `False` in the settings.
        plugin_sorting_order (dict): A dict containing a custom sorting orders for plugins. The keys are plugin identifiers,
            mapped to dictionaries containing the sorting contexts as key and the custom sorting value as value.
        plugin_blacklist (list): A list of plugin identifiers/identifier-requirement tuples
            that are currently blacklisted.
        plugin_restart_needing_hooks (list): A list of hook namespaces which cause a plugin to need a restart in order
            be enabled/disabled. Does not have to contain full hook identifiers, will be matched with glob patterns. If
            not provided this defaults to `octoprint.server.http.*`, `octoprint.printer.factory`,
            `octoprint.access.permissions` and `octoprint.timelapse.extensions`.
        plugin_obsolete_hooks (list): A list of hooks that have been declared obsolete. Plugins implementing them will
            not be enabled since they might depend on functionality that is no longer available. If not provided this
            defaults to `octoprint.comm.protocol.gcode`.
        plugin_considered_bundled (list): A list of plugin identifiers that are considered bundled plugins even if
            installed separately. If not provided this defaults to `firmware_check`, `file_check` and `pi_support`.
        plugin_validators (list): A list of additional plugin validators through which to process each plugin.
        compatibility_ignored_list (list): A list of plugin keys for which it will be ignored if they are flagged as
            incompatible. This is for development purposes only and should not be used in production.

    Returns:
        (octoprint.plugin.core.PluginManager): A fully initialized `PluginManager` instance to be used for plugin
            management tasks.

    Raises:
        ValueError: `init` was `True` although the plugin manager was already initialized, or it was `False` although
            the plugin manager was not yet initialized.
    """

    global _instance
    if _instance is not None:
        if init:
            raise ValueError("Plugin Manager already initialized")

    else:
        if init:
            if plugin_bases is None:
                plugin_bases = [OctoPrintPlugin]

            if plugin_restart_needing_hooks is None:
                plugin_restart_needing_hooks = [
                    "octoprint.server.http.*",
                    "octoprint.printer.factory",
                    "octoprint.access.permissions",
                    "octoprint.timelapse.extensions",
                ]  # if changed update docs above!

            if plugin_obsolete_hooks is None:
                plugin_obsolete_hooks = [
                    "octoprint.comm.protocol.gcode"
                ]  # if changed update docs above!

            if plugin_considered_bundled is None:
                plugin_considered_bundled = [
                    "firmware_check",
                    "file_check",
                    "pi_support",
                ]  # if changed update docs above!

            if plugin_validators is None:
                plugin_validators = [_validate_plugin]
            else:
                plugin_validators.append(_validate_plugin)

            _instance = PluginManager(
                plugin_folders,
                plugin_bases,
                plugin_entry_points,
                logging_prefix="octoprint.plugins.",  # if changed update docs above!
                plugin_disabled_list=plugin_disabled_list,
                plugin_sorting_order=plugin_sorting_order,
                plugin_blacklist=plugin_blacklist,
                plugin_restart_needing_hooks=plugin_restart_needing_hooks,
                plugin_obsolete_hooks=plugin_obsolete_hooks,
                plugin_considered_bundled=plugin_considered_bundled,
                plugin_validators=plugin_validators,
                compatibility_ignored_list=compatibility_ignored_list,
            )
        else:
            raise ValueError("Plugin Manager not initialized yet")
    return _instance


def plugin_settings(
    plugin_key,
    defaults=None,
    get_preprocessors=None,
    set_preprocessors=None,
    settings=None,
):
    """
    Factory method for creating a `PluginSettings` instance.

    Arguments:
        plugin_key (str): The plugin identifier for which to create the settings instance.
        defaults (dict): The default settings for the plugin, if different from get_settings_defaults.
        get_preprocessors (dict): The getter preprocessors for the plugin.
        set_preprocessors (dict): The setter preprocessors for the plugin.
        settings (octoprint.settings.Settings): The settings instance to use.

    Returns:
        (octoprint.plugin.PluginSettings): A fully initialized `PluginSettings` instance to be used to access the plugin's
            settings
    """
    if settings is None:
        settings = s()
    return PluginSettings(
        settings,
        plugin_key,
        defaults=defaults,
        get_preprocessors=get_preprocessors,
        set_preprocessors=set_preprocessors,
    )


def plugin_settings_for_settings_plugin(plugin_key, instance, settings=None):
    """
    Factory method for creating a `PluginSettings` instance for a given `SettingsPlugin` instance.

    Will return `None` if the provided `instance` is not a [SettingsPlugin][octoprint.plugin.types.SettingsPlugin] instance.

    Arguments:
        plugin_key (string): The plugin identifier for which to create the settings instance.
        instance (octoprint.plugin.types.SettingsPlugin): The `SettingsPlugin` instance.
        settings (octoprint.settings.Settings): The settings instance to use. Defaults to the global OctoPrint settings.

    Returns:
        (octoprint.plugin.PluginSettings | None): A fully initialized `PluginSettings` instance to be used to access the plugin's
            settings, or `None` if the provided `instance` was not a `SettingsPlugin`
    """
    if not isinstance(instance, SettingsPlugin):
        return None

    try:
        get_preprocessors, set_preprocessors = instance.get_settings_preprocessors()
    except Exception:
        logging.getLogger(__name__).exception(
            f"Error while retrieving preprocessors for plugin {plugin_key}"
        )
        return None

    return plugin_settings(
        plugin_key,
        get_preprocessors=get_preprocessors,
        set_preprocessors=set_preprocessors,
        settings=settings,
    )


def call_plugin(
    types,
    method,
    args=None,
    kwargs=None,
    callback=None,
    error_callback=None,
    sorting_context=None,
    initialized=True,
    manager=None,
):
    """
    Helper method to invoke the indicated `method` on all registered plugin implementations implementing the
    indicated `types`. Allows providing method arguments and registering callbacks to call in case of success
    and/or failure of each call which can be used to return individual results to the calling code.

    Example:

    ``` python
    def my_success_callback(name, plugin, result):
        print("{name} was called successfully and returned {result!r}".format(**locals()))

    def my_error_callback(name, plugin, exc):
        print("{name} raised an exception: {exc!s}".format(**locals()))

    octoprint.plugin.call_plugin(
        [octoprint.plugin.StartupPlugin],
        "on_startup",
        args=(my_host, my_port),
        callback=my_success_callback,
        error_callback=my_error_callback
    )
    ```

    Arguments:
        types (list): A list of plugin implementation types to match against.
        method (str): Name of the method to call on all matching implementations.
        args (tuple): A tuple containing the arguments to supply to the called `method`. Optional.
        kwargs (dict): A dictionary containing the keyword arguments to supply to the called `method`. Optional.
        callback (callable): A callback to invoke after an implementation has been called successfully. Will be called
            with the three arguments `name`, `plugin` and `result`. `name` will be the plugin identifier,
            `plugin` the plugin implementation instance itself and `result` the result returned from the
            `method` invocation.
        error_callback (callable): A callback to invoke after the call of an implementation resulted in an exception.
            Will be called with the three arguments `name`, `plugin` and `exc`. `name` will be the plugin
            identifier, `plugin` the plugin implementation instance itself and `exc` the caught exception.
        initialized (bool): Ignored.
        manager (octoprint.plugin.core.PluginManager | None): The plugin manager to use. If not provided, the global plugin manager
    """

    if not isinstance(types, (list, tuple)):
        types = [types]
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    if manager is None:
        manager = plugin_manager()

    logger = logging.getLogger(__name__)

    plugins = manager.get_implementations(*types, sorting_context=sorting_context)
    for plugin in plugins:
        if not hasattr(plugin, "_identifier"):
            continue

        if hasattr(plugin, method):
            logger.debug(f"Calling {method} on {plugin._identifier}")
            try:
                result = getattr(plugin, method)(*args, **kwargs)
                if callback:
                    callback(plugin._identifier, plugin, result)
            except Exception as exc:
                logger.exception(
                    "Error while calling plugin %s" % plugin._identifier,
                    extra={"plugin": plugin._identifier},
                )
                if error_callback:
                    error_callback(plugin._identifier, plugin, exc)


class PluginSettings:
    """
    The `PluginSettings` class is the interface for plugins to their own or globally defined settings.

    It provides some convenience methods for directly accessing plugin settings via the regular
    [Settings][octoprint.settings.Settings] interfaces as well as means to access plugin specific folder locations.

    All getter and setter methods will ensure that plugin settings are stored in their correct location within the
    settings structure by modifying the supplied paths accordingly.

    Arguments:
        settings (octoprint.settings.Settings): The `Settings` instance on which to operate.
        plugin_key (str): The plugin identifier of the plugin for which to create this instance.
        defaults (dict): The plugin's defaults settings.
        get_preprocessors (dict): The plugin's get preprocessors. A dict of settings paths to callables that will
            be called with the value of the setting and should return the processed value.
        set_preprocessors (dict): The plugin's set preprocessors. A dict of settings paths to callables that will
            be called with the value of the setting and should return the processed value.
    """

    def __init__(
        self,
        settings,
        plugin_key,
        defaults=None,
        get_preprocessors=None,
        set_preprocessors=None,
    ):
        self.settings = settings
        """ The `Settings` instance on which to operate. """

        self.plugin_key = plugin_key
        """ The plugin identifier of the plugin for which this instance was created. """

        self.defaults = None
        """ The plugin's defaults settings, prefixed with the plugin's settings path. """

        if defaults is not None:
            self.defaults = {"plugins": {}}
            self.defaults["plugins"][plugin_key] = defaults
            self.defaults["plugins"][plugin_key]["_config_version"] = None

        self.get_preprocessors = {"plugins": {}}
        """ The plugin's get preprocessors, prefixed with the plugin's settings path. """

        if get_preprocessors is None:
            get_preprocessors = {}
        self.get_preprocessors["plugins"][plugin_key] = get_preprocessors

        self.set_preprocessors = {"plugins": {}}
        """ The plugin's set preprocessors, prefixed with the plugin's settings path. """

        if set_preprocessors is None:
            set_preprocessors = {}
        self.set_preprocessors["plugins"][plugin_key] = set_preprocessors

    def _prefix_path(self, path=None):
        if path is None:
            path = list()
        return ["plugins", self.plugin_key] + path

    def _add_getter_kwargs(self, kwargs):
        if "defaults" not in kwargs and self.defaults is not None:
            kwargs.update(defaults=self.defaults)
        if "preprocessors" not in kwargs:
            kwargs.update(preprocessors=self.get_preprocessors)
        return kwargs

    def _add_setter_kwargs(self, kwargs):
        if "defaults" not in kwargs and self.defaults is not None:
            kwargs.update(defaults=self.defaults)
        if "preprocessors" not in kwargs:
            kwargs.update(preprocessors=self.set_preprocessors)
        return kwargs

    def _wrap_overlay(self, args):
        result = list(args)
        overlay = result[0]
        result[0] = {"plugins": {self.plugin_key: overlay}}
        return result

    def has(self, path, **kwargs):
        """
        Checks whether a value for `path` is present in the settings.

        Arguments:
            path (list, tuple): The path for which to check the value.

        Returns:
            (bool): Whether a value for `path` is present in the settings.
        """
        return self.settings.has(
            self._prefix_path(path), **self._add_getter_kwargs(kwargs)
        )

    def get(self, path, **kwargs):
        """
        Retrieves a raw value from the settings for `path`, optionally merging the raw value with the default settings
        if `merged` is set to True.

        Arguments:
            path (list, tuple): The path for which to retrieve the value.
            merged (bool): Whether to merge the returned result with the default settings (True) or not (False,
                default).
            asdict (bool): Whether to return the result as a dictionary (True) or not (False, default).

        Returns:
            (object): The retrieved settings value.
        """
        return self.settings.get(
            self._prefix_path(path), **self._add_getter_kwargs(kwargs)
        )

    def get_int(self, path, **kwargs):
        """
        Like `get` but tries to convert the retrieved value to [int][]. If `min` is provided and the retrieved
        value is less than it, it will be returned instead of the value. Likewise for `max` - it will be returned if
        the value is greater than it.

        Arguments:
            path (list, tuple): The path for which to retrieve the value.
            min (int): The minimum value to return.
            max (int): The maximum value to return.

        Returns:
            (int | None): The retrieved settings value, converted to an integer, if possible, `None` otherwise
        """
        return self.settings.getInt(
            self._prefix_path(path), **self._add_getter_kwargs(kwargs)
        )

    def get_float(self, path, **kwargs):
        """
        Like `get` but tries to convert the retrieved value to [float][]. If `min` is provided and the retrieved
        value is less than it, it will be returned instead of the value. Likewise for `max` - it will be returned if
        the value is greater than it.

        Arguments:
            path (list, tuple): The path for which to retrieve the value.
            min (float): The minimum value to return.
            max (float): The maximum value to return.

        Returns:
            (float | None): The retrieved settings value, converted to a float, if possible, `None` otherwise
        """
        return self.settings.getFloat(
            self._prefix_path(path), **self._add_getter_kwargs(kwargs)
        )

    def get_boolean(self, path, **kwargs):
        """
        Like `get` but tries to convert the retrieved value to [bool][].

        Arguments:
            path (list, tuple): The path for which to retrieve the value.

        Returns:
            (bool | None): The retrieved settings value, converted to a boolean, if possible, `None` otherwise
        """
        return self.settings.getBoolean(
            self._prefix_path(path), **self._add_getter_kwargs(kwargs)
        )

    def set(self, path, value, **kwargs):
        """
        Sets the raw value on the settings for `path`.

        Arguments:
            path (list, tuple): The path for which to set the value.
            value (object): The value to set.
            force (bool): If set to True, the modified configuration will be written back to disk even if
                the value didn't change.
        """
        return self.settings.set(
            self._prefix_path(path), value, **self._add_setter_kwargs(kwargs)
        )

    def set_int(self, path, value, **kwargs):
        """
        Like `set` but ensures the value is an [int][] through attempted conversion before setting it.

        If `min` and/or `max` are provided, it will also be ensured that the value is greater than or equal
        to `min` and less than or equal to `max`. If that is not the case, the limit value (`min` if less than
        that, `max` if greater than that) will be set instead.

        Arguments:
            path (list, tuple): The path for which to set the value.
            value (object): The value to set.
            min (int): The minimum value to set.
            max (int): The maximum value to set.
        """
        return self.settings.setInt(
            self._prefix_path(path), value, **self._add_setter_kwargs(kwargs)
        )

    def set_float(self, path, value, **kwargs):
        """
        Like `set` but ensures the value is an [float][] through attempted conversion before setting it.

        If `min` and/or `max` are provided, it will also be ensured that the value is greater than or equal
        to `min` and less than or equal to `max`. If that is not the case, the limit value (`min` if less than
        that, `max` if greater than that) will be set instead.

        Arguments:
            path (list, tuple): The path for which to set the value.
            value (object): The value to set.
            min (float): The minimum value to set.
            max (float): The maximum value to set.
        """
        return self.settings.setFloat(
            self._prefix_path(path), value, **self._add_setter_kwargs(kwargs)
        )

    def set_boolean(self, path, value, **kwargs):
        """
        Like `set` but ensures the value is an [bool][] through attempted conversion before setting it.

        Arguments:
            path (list, tuple): The path for which to set the value.
            value (object): The value to set.
        """
        return self.settings.setBoolean(
            self._prefix_path(path), value, **self._add_setter_kwargs(kwargs)
        )

    def remove(self, path, **kwargs):
        """
        Removes the value for `path` from the settings.

        Arguments:
            path (list, tuple): The path for which to remove the value.
        """
        return self.settings.remove(self._prefix_path(path), **kwargs)

    def add_overlay(self, overlay, **kwargs):
        """
        Adds an overlay for th plugin to the settings.

        Arguments:
            overlay (dict): The overlay to add.

        Returns:
            (str): The key under which the overlay was added.
        """
        return self.settings.add_overlay(self._wrap_overlay(overlay), **kwargs)

    def remove_overlay(self, key):
        """
        Removes an overlay from the settings by `key`.

        Arguments:
            key (str): The key of the overlay to remove.
        """
        return self.settings.remove_overlay(key)

    def global_has(self, path, **kwargs):
        """
        Checks whether the global settings structure has a value for `path`.

        Directly forwards to [octoprint.settings.Settings.has][].
        """
        return self.settings.has(path, **kwargs)

    def global_remove(self, path, **kwargs):
        """
        Removes the value for `path` from the global settings structure.

        Directly forwards to [octoprint.settings.Settings.remove][].
        """
        return self.settings.remove(path, **kwargs)

    def global_get(self, path, **kwargs):
        """
        Gets a value from the global settings structure.

        Directly forwards to [octoprint.settings.Settings.get][]. See its documentation for possible
        parameters.
        """
        return self.settings.get(path, **kwargs)

    def global_get_int(self, path, **kwargs):
        """
        Gets a value from the global settings structure and tries to convert it to [int][].

        Directly forwards to [octoprint.settings.Settings.getInt][]. See its documentation for possible
        parameters.
        """
        return self.settings.getInt(path, **kwargs)

    def global_get_float(self, path, **kwargs):
        """
        Gets a value from the global settings structure and tries to convert it to [float][].

        Directly forwards to [octoprint.settings.Settings.getFloat][]. See its documentation for possible
        parameters.
        """
        return self.settings.getFloat(path, **kwargs)

    def global_get_boolean(self, path, **kwargs):
        """
        Gets a value from the global settings structure and tries to convert it to [bool][].

        Directly forwards to [octoprint.settings.Settings.getBoolean][]. See its documentation for possible
        parameters.
        """
        return self.settings.getBoolean(path, **kwargs)

    def global_set(self, path, value, **kwargs):
        """
        Sets a value in the global settings structure.

        Directly forwards to [octoprint.settings.Settings.set][]. See its documentation for possible
        parameters.
        """
        self.settings.set(path, value, **kwargs)

    def global_set_int(self, path, value, **kwargs):
        """
        Sets a value in the global settings structure and tries to convert it to [int][].

        Directly forwards to [octoprint.settings.Settings.setInt][]. See its documentation for possible
        parameters.
        """
        self.settings.setInt(path, value, **kwargs)

    def global_set_float(self, path, value, **kwargs):
        """
        Sets a value in the global settings structure and tries to convert it to [float][].

        Directly forwards to [octoprint.settings.Settings.setFloat][]. See its documentation for possible
        parameters.
        """
        self.settings.setFloat(path, value, **kwargs)

    def global_set_boolean(self, path, value, **kwargs):
        """
        Sets a value in the global settings structure and tries to convert it to [bool][].

        Directly forwards to [octoprint.settings.Settings.setBoolean][]. See its documentation for possible
        parameters.
        """
        self.settings.setBoolean(path, value, **kwargs)

    def global_get_basefolder(self, folder_type, **kwargs):
        """
        Retrieves a globally defined basefolder of the given `folder_type`.

        Directly forwards to [octoprint.settings.Settings.getBaseFolder][].
        """
        return self.settings.getBaseFolder(folder_type, **kwargs)

    def get_plugin_logfile_path(self, postfix=None):
        """
        Retrieves the path to a logfile specifically for the plugin.

        If `postfix` is not supplied, the logfile will be named `plugin_<plugin identifier>.log` and located within the
        configured `logs` folder. If a postfix is supplied, the name will be `plugin_<plugin identifier>_<postfix>.log`
        at the same location.

        Plugins may use this for specific logging tasks. For example, a [octoprint.plugin.types.SlicerPlugin][] might
        want to create a log file for logging the output of the slicing engine itself if some debug flag is set.

        Arguments:
            postfix (str): Postfix of the logfile for which to create the path. If set, the file name of the log file
                will be `plugin_<plugin identifier>_<postfix>.log`, if not it will be `plugin_<plugin identifier>.log`.

        Returns:
            (str): Absolute path to the log file, directly usable by the plugin.
        """
        filename = "plugin_" + self.plugin_key
        if postfix is not None:
            filename += "_" + postfix
        filename += ".log"
        return os.path.join(self.settings.getBaseFolder("logs"), filename)

    @deprecated(
        "PluginSettings.get_plugin_data_folder has been replaced by OctoPrintPlugin.get_plugin_data_folder",
        includedoc="Replaced by :func:`~octoprint.plugin.types.OctoPrintPlugin.get_plugin_data_folder`",
        since="1.2.0",
    )
    def get_plugin_data_folder(self):
        path = os.path.join(self.settings.getBaseFolder("data"), self.plugin_key)
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    @deprecated(
        "getInt has been renamed to get_int",
        includedoc="Replaced by [octoprint.plugin.types.OctoPrintPlugin.get_int][]",
    )
    def getInt(self, *args, **kwargs):
        return self.get_int(*args, **kwargs)

    @deprecated(
        "getFloat has been renamed to get_float",
        includedoc="Replaced by [octoprint.plugin.types.OctoPrintPlugin.get_float][]",
    )
    def getFloat(self, *args, **kwargs):
        return self.get_float(*args, **kwargs)

    @deprecated(
        "getBoolean has been renamed to get_boolean",
        includedoc="Replaced by [octoprint.plugin.types.OctoPrintPlugin.get_boolean][]",
    )
    def getBoolean(self, *args, **kwargs):
        return self.get_boolean(*args, **kwargs)

    @deprecated(
        "setInt has been renamed to set_int",
        includedoc="Replaced by [octoprint.plugin.types.OctoPrintPlugin.set_int][]",
    )
    def setInt(self, *args, **kwargs):
        return self.set_int(*args, **kwargs)

    @deprecated(
        "setFloat has been renamed to set_float",
        includedoc="Replaced by [octoprint.plugin.types.OctoPrintPlugin.set_float][]",
    )
    def setFloat(self, *args, **kwargs):
        return self.set_float(*args, **kwargs)

    @deprecated(
        "setBoolean has been renamed to set_boolean",
        includedoc="Replaced by [octoprint.plugin.types.OctoPrintPlugin.set_boolean][]",
    )
    def setBoolean(self, *args, **kwargs):
        return self.set_boolean(*args, **kwargs)

    def get_all_data(self, **kwargs):
        """
        Returns all data stored for this plugin.

        Arguments:
            merged (bool): Whether to merge the data with the defaults. Defaults to `True`.
            asdict (bool): Whether to return the data as a dict. Defaults to `True`.
            defaults (bool): Which defaults to use. Defaults to the plugin defaults.
            preprocessors (list): List of preprocessors to apply to the data. Defaults to the plugin preprocessors.
        """
        merged = kwargs.get("merged", True)
        asdict = kwargs.get("asdict", True)
        defaults = kwargs.get("defaults", self.defaults)
        preprocessors = kwargs.get("preprocessors", self.get_preprocessors)

        kwargs.update(
            {
                "merged": merged,
                "asdict": asdict,
                "defaults": defaults,
                "preprocessors": preprocessors,
            }
        )

        return self.settings.get(self._prefix_path(), **kwargs)

    def clean_all_data(self):
        """
        Removes all data stored for this plugin.
        """
        self.settings.remove(self._prefix_path())

    def __getattr__(self, item):
        return getattr(self.settings, item)
