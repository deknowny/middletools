import asyncio

import middletools


async def middleware1(request, call_next):
    print(f"Run middleware1 (request: {request})")
    response = await call_next()
    print(f"End middleware1 (response: {response})")
    return response


async def middleware2(request, call_next):
    print(f"Run middleware2 (request: {request})")
    response = await call_next()
    print(f"End middleware2 (response: {response})")
    return response


async def main():
    read_afterwords = await middletools.read_forewords(
        middleware1, middleware2,
        inbox_value=123  # Pass `request` value
    )
    print("Some other code...")
    await read_afterwords(456)  # Pass `response` value


asyncio.run(main())