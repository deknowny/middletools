try:
    import importlib.metadata as metadata
except ImportError:
    import importlib as metadata

from middlewares import types
from middlewares.book import read_forewords
from middlewares.exceptions import CallNextNotUsedError


__version__ = metadata.version(__name__)
__all__ = ["read_forewords", "CallNextNotUsedError", "types"]

del metadata
