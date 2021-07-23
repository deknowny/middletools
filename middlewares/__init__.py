import pkg_resources

from middlewares import types
from middlewares.book import read_forewords
from middlewares.exceptions import CallNextNotUsedError, NothingReturnedError


__version__ = pkg_resources.get_distribution(__name__).version
__all__ = ["read_forewords", "CallNextNotUsedError", "types"]

del pkg_resources
