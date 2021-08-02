import typing


class InboxType:
    pass


class OutboxType:
    pass


class MockPayload(typing.NamedTuple):
    value: typing.Any
    stamp: float
