import asyncio
import enum
import typing

from middlewares.exceptions import CallNextNotUsedError
from middlewares.types import MiddlewareHandler, InboxType, OutboxType


async def read_forewords(
    *middlewares: MiddlewareHandler[InboxType, OutboxType], inbox_value: InboxType
) -> typing.Callable[[OutboxType], typing.Awaitable[OutboxType]]:
    twitched_middlewares: typing.List[_MiddlewareDispatchingInfo] = []
    for middleware in middlewares:
        call_next_give_control = asyncio.Future()
        call_next_return_control = asyncio.Future()
        call_next = _call_next_bounder(call_next_give_control, call_next_return_control)
        middleware_dispatching = asyncio.create_task(middleware(inbox_value, call_next))
        # Wait when middleware call `call_next` or not called at all
        giving_control_reason = await call_next_give_control
        if giving_control_reason == _GiveControlReason.CALL_NEXT_IGNORED:
            raise CallNextNotUsedError(
                f"Middleware {middleware} doesn't call `call_next`, "
                f"dispatching declined forcibly"
            )
        else:
            twitched_middlewares.append(
                _MiddlewareDispatchingInfo(
                    running_task=middleware_dispatching,
                    call_next_return_control=call_next_return_control,
                )
            )

    return _read_afterwords_bounder(*twitched_middlewares)


# I can use just `asyncio.FIRST_COMPLETED` or just set an exception,
# but this approach is more readable
class _GiveControlReason(enum.Enum):
    CALL_NEXT_USED = enum.auto()
    CALL_NEXT_IGNORED = enum.auto()


class _MiddlewareDispatchingInfo(typing.NamedTuple):
    running_task: asyncio.Task
    call_next_return_control: asyncio.Future


def _call_next_bounder(
    call_next_give_control: asyncio.Future, call_next_return_control: asyncio.Future
):
    async def call_next():
        call_next_give_control.set_result(_GiveControlReason.CALL_NEXT_USED)
        outbox_value = await call_next_return_control
        return outbox_value

    return call_next


async def _done_mock(
    call_next_give_control: asyncio.Future,
    call_next_return_control: asyncio.Future,
    middleware: MiddlewareHandler[InboxType, OutboxType],
    inbox_value: InboxType,
) -> None:
    call_next = _call_next_bounder(call_next_give_control, call_next_return_control)
    await middleware(inbox_value, call_next)

    # If `call_next` hasn't been called
    if not call_next_give_control.done():
        call_next_give_control.set_result(_GiveControlReason.CALL_NEXT_IGNORED)


def _read_afterwords_bounder(*twitched_middlewares: _MiddlewareDispatchingInfo):
    async def read_afterword(outbox_value):
        for dispatching_info in reversed(twitched_middlewares):
            dispatching_info.call_next_return_control.set_result(outbox_value)
            await dispatching_info.running_task

    return read_afterword
