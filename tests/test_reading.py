import time
import typing
import unittest.mock

import pytest

import middlewares
from tests.types import InboxType, MockPayload, OutboxType


@pytest.mark.asyncio
async def test_normal_case():
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
    ) -> OutboxType:
        middleware2_before_call(MockPayload(inbox, time.monotonic()))
        outbox = await call_next()
        middleware2_after_call(MockPayload(outbox, time.monotonic()))
        return outbox

    inbox_value = InboxType()
    outbox_value = OutboxType()

    # Step: 1
    read_afterword = await middlewares.read_forewords(
        middleware1, middleware2, inbox_value=inbox_value
    )

    # Check middlewares has been run and stopped at `call_next`
    middleware1_before_call.assert_called_once()
    middleware2_before_call.assert_called_once()
    middleware1_after_call.assert_not_called()
    middleware2_after_call.assert_not_called()

    middleware1_run_info: MockPayload = middleware1_before_call.call_args[0][
        0
    ]
    middleware2_run_info: MockPayload = middleware2_before_call.call_args[0][
        0
    ]

    # Middleware2 called later
    assert middleware1_run_info.stamp < middleware2_run_info.stamp

    # Inbox value has been passed
    assert (
        middleware1_run_info.value
        == middleware2_run_info.value
        == inbox_value
    )

    # Step: 2
    await read_afterword(outbox_value)
    middleware1_before_call.assert_called_once()
    middleware2_before_call.assert_called_once()
    middleware1_after_call.assert_called_once()
    middleware2_after_call.assert_called_once()

    middleware1_run_info: MockPayload = middleware1_after_call.call_args[0][0]
    middleware2_run_info: MockPayload = middleware2_after_call.call_args[0][0]

    # Middleware2 called earlier
    assert middleware1_run_info.stamp > middleware2_run_info.stamp
    # Outbox value has been passed
    assert (
        middleware1_run_info.value
        == middleware2_run_info.value
        == outbox_value
    )
