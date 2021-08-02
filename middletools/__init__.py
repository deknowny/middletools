import pkg_resources

from middletools import types
from middletools.book import read_forewords
from middletools.exceptions import CallNextNotUsedError, NothingReturnedError

__version__ = pkg_resources.get_distribution(__name__).version
__all__ = ["read_forewords", "CallNextNotUsedError", "NothingReturnedError", "types"]

del pkg_resources
