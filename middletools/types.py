import abc
import typing

InboxType = typing.TypeVar("InboxType")
OutboxType = typing.TypeVar("OutboxType")

CallNext = typing.Callable[[], OutboxType]
MiddlewareHandler = typing.Callable[
    [InboxType, CallNext], typing.Awaitable[OutboxType]
]
