import time
import typing
import unittest.mock

import pytest

import middlewares
from tests.types import InboxType, MockPayload, OutboxType


@pytest.mark.asyncio
async def test_not_called_call_next():
    middleware1_before_call = unittest.mock.Mock()
    middleware1_after_call = unittest.mock.Mock()
    middleware2_before_call = unittest.mock.Mock()

    async def middleware1(
        inbox: InboxType, call_next: middlewares.types.CallNext
    ) -> OutboxType:
        middleware1_before_call(MockPayload(inbox, time.monotonic()))
        outbox = await call_next()
        middleware1_after_call(MockPayload(outbox, time.monotonic()))
        return outbox

    async def middleware2(
        inbox: InboxType, call_next: middlewares.types.CallNext
    ) -> OutboxType:
        middleware2_before_call(MockPayload(inbox, time.monotonic()))
        return OutboxType()

    inbox_value = InboxType()
    with pytest.raises(middlewares.CallNextNotUsedError) as error:
        read_afterwords = await middlewares.read_forewords(
            middleware1, middleware2, inbox_value=inbox_value
        )

    middleware1_before_call.assert_called_once()
    middleware1_after_call.assert_not_called()
    middleware2_before_call.assert_called_once()

    assert error.value.middleware == middleware2
    assert repr(error.value)  # Formatting is OK


@pytest.mark.asyncio
async def test_not_returned():
    middleware1_before_call = unittest.mock.Mock()
    middleware1_after_call = unittest.mock.Mock()
    middleware2_before_call = unittest.mock.Mock()
    middleware2_after_call = unittest.mock.Mock()

    async def middleware1(
        inbox: InboxType, call_next: middlewares.types.CallNext
    ) -> OutboxType:
        middleware1_before_call(MockPayload(inbox, time.monotonic()))
        outbox = await call_next()
        middleware1_after_call(MockPayload(outbox, time.monotonic()))
        return outbox

    async def middleware2(
        inbox: InboxType, call_next: middlewares.types.CallNext
    ) -> typing.Optional[OutboxType]:
        middleware2_before_call(MockPayload(inbox, time.monotonic()))
        outbox = await call_next()
        middleware2_after_call(MockPayload(outbox, time.monotonic()))

    inbox_value = InboxType()
    outbox_value = OutboxType()
    read_afterwords = await middlewares.read_forewords(
        middleware1, middleware2, inbox_value=inbox_value
    )

    middleware1_before_call.assert_called_once()
    middleware1_after_call.assert_not_called()
    middleware2_before_call.assert_called_once()
    middleware2_after_call.assert_not_called()

    with pytest.raises(middlewares.NothingReturnedError) as error:
        await read_afterwords(outbox_value)

    middleware1_before_call.assert_called_once()
    middleware1_after_call.assert_not_called()
    middleware2_before_call.assert_called_once()
    middleware2_after_call.assert_called_once()

    assert error.value.middleware == middleware2
    assert repr(error.value)  # Formatting is OK
