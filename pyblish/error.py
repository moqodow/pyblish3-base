class PyblishError(Exception):
    """Baseclass for all Pyblish exceptions"""


class CollectionError(PyblishError):
    """Baseclass for collection errors"""


class ValidationError(PyblishError):
    """Baseclass for validation errors"""


class ExtractionError(PyblishError):
    """Baseclass for extraction errors"""


class IntegrationError(PyblishError):
    """Baseclass for integration errors"""


class NoInstancesError(Exception):
    """Raised if no instances could be found"""
