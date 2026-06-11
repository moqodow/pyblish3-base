import importlib.metadata

version = importlib.metadata.version("pyblish3-base")
version_major, version_minor, version_patch, *_ = version.split(".")
version_info = (int(version_major), int(version_minor), int(version_patch))
__version__ = version

__all__ = ['version', 'version_info', '__version__']
