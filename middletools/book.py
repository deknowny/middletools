import asyncio
import enum
import sys
import typing

from middletools.exceptions import CallNextNotUsedError, NothingReturnedError
from middletools.types import InboxType, MiddlewareHandler, OutboxType

_should_show_cancel_message = sys.version_info >= (3, 9)


async def read_forewords(
    *middlewares: MiddlewareHandler[InboxType, OutboxType],
    inbox_value: InboxType,
) -> typing.Callable[[OutboxType], typing.Awaitable[OutboxType]]:
    twitched_middlewares: typing.List[_MiddlewareDispatchingInfo] = []
    for middleware in middlewares:
        call_next_give_control: asyncio.Future = asyncio.Future()
        call_next_return_control: asyncio.Future = asyncio.Future()
        middleware_dispatching = asyncio.create_task(
            _done_mock(
                call_next_give_control,
                call_next_return_control,
                middleware,
                inbox_value,
            )
        )
        # Wait when middleware call `call_next` or not called at all
        giving_control_reason = await call_next_give_control
        if giving_control_reason == _GiveControlReason.CALL_NEXT_IGNORED:
            # Should cancel tasks otherwise get warnings
            await _cancel_tasks(
                *twitched_middlewares,
                message=(
                    "Middleware dispatching stopped because"
                    f"{middleware} doesn't call `call_next`'"
                ),
            )
            raise CallNextNotUsedError(middleware)
        else:
            twitched_middlewares.append(
                _MiddlewareDispatchingInfo(
                    middleware=middleware,
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
    middleware: MiddlewareHandler
    running_task: asyncio.Task
    call_next_return_control: asyncio.Future


async def _cancel_tasks(
    *dispatching_info: _MiddlewareDispatchingInfo, message: str
):
    for info in dispatching_info:
        try:
            if _should_show_cancel_message:
                info.running_task.cancel(message)  # type: ignore
            else:
                info.running_task.cancel()
            await info.running_task
        except asyncio.CancelledError:
            pass


def _call_next_bounder(
    call_next_give_control: asyncio.Future,
    call_next_return_control: asyncio.Future,
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
) -> OutboxType:
    call_next = _call_next_bounder(
        call_next_give_control, call_next_return_control
    )
    middleware_result = await middleware(inbox_value, call_next)

    # If `call_next` hasn't been called
    if not call_next_give_control.done():
        call_next_give_control.set_result(
            _GiveControlReason.CALL_NEXT_IGNORED
        )

    return middleware_result


def _read_afterwords_bounder(
    *twitched_middlewares: _MiddlewareDispatchingInfo,
):
    async def read_afterword(outbox_value):
        for dispatching_info in reversed(twitched_middlewares):
            dispatching_info.call_next_return_control.set_result(outbox_value)
            middleware_result = await dispatching_info.running_task
            if middleware_result is None:
                # Should cancel tasks otherwise get warnings
                await _cancel_tasks(
                    *twitched_middlewares,
                    message=(
                        "Middleware dispatching stopped because"
                        f"{dispatching_info.middleware} returns nothing"
                    ),
                )
                raise NothingReturnedError(dispatching_info.middleware)

    return read_afterword
