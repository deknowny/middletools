import dataclasses

from middlewares.types import MiddlewareHandler


@dataclasses.dataclass(frozen=True, repr=False)
class _ContainMiddleware(Exception):
    middleware: MiddlewareHandler

    __slots__ = ("middleware",)


class CallNextNotUsedError(_ContainMiddleware):
    def __repr__(self):
        return (
            f"Middleware {self.middleware} doesn't call `call_next`, "
            f"dispatching declined forcibly"
        )


class NothingReturnedError(_ContainMiddleware):
    def __repr__(self):
        return (
            f"Middleware {self.middleware} "
            f"returned nothing. Decline dispatching"
        )
