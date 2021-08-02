# Middletools
[![Coverage Status](https://coveralls.io/repos/github/deknowny/middletools/badge.svg)](https://coveralls.io/github/deknowny/middletools)
![Supported python version](https://img.shields.io/pypi/pyversions/middletools)
![PyPI package version](https://img.shields.io/pypi/v/middletools)
![Downloads](https://img.shields.io/pypi/dm/middletools)


This is a python library that allows you to integrate middlewares-based system to your project. It contains base tools for creating and running middlewares with `async-await` style

```python
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
```
Output is
```
Run middleware1 (request: 123)
Run middleware2 (request: 123)
Some other code...
End middleware2 (response: 456)
End middleware1 (response: 456)
```


## Installation
### PyPI
```shell
python -m pip install middletools
```
### GitHub
```shell
python -m pip install https://github.com/deknowny/middlewares/archive/main.zip
```

## Usage
The main idea is give an ability just passing the middlewares and `inbox`/`outbox` payload values in a few methods instead of running and saving middlewares state by hand

Standard case: a function runs RESTful API routers and requires a middleware that checks
a header in client's request

***
There are 2 endpoints for an abstract `GET` and `POST` methods
```python
# Some abstract router
@router.get("/")
async def route_get(request):
    return 200, {"response": "some content"}


@router.post("/")
async def route_post(request):
    return 201, {"response": "ok"}

```

In the core of web framework you used a function like this that just call all routers

```python
class Router:
    ...
    ...
    
    async def call_routers(self, request):
        for router in self.routers:
            ... # Pass request to routers and check it matched
```

`middlewares` library allows you easy integrate middleware system to your `call_routers`
***
### Create middleware function
```python
import middletools

...
...

# Adding a middleware handler to an abstract 
@router.add_middleware
async def my_middleware(
    request: SomeRequest, call_next: middletools.types.CallNext
) -> SomeResponse:
    # Just check if header exists, id not set the default value
    if "X-Required-Header" not in request.headers:
        request.header["X-Required-Header"] = "default"
    response = await call_next()
    return response
```
Here we add a header to client request if clint didn't do it. Then `await call_next()` give control to other middlewares or to our `call_routers` handler and response from this is the value `call_next()` returns
***
`call_routers` should looks like this 
```python
import typing

import middletools


class Router:
    # You can use generics to describe middleware hand;er
    middlewares: typing.List[
        middletools.types.MiddlewareHandler[
            SomeRequest, SomeResponse
        ]
    ]
    ...
    ...

    async def call_routers(self, request):
        read_afterwords = await middletools.read_forewords(
            *self.middlewares, inbox_value=request
        )
        for router in self.routers:
            ... # Pass request to routers and check it matched
            response = ...
            await read_afterwords(response)
            break
        
```
`middlewares.read_forewords` run middlewares until every one of them give control with `await call_next()`.
When we do all our stuff and get the router response we can call `await read_afterwords(response)` and run all middlewares completely.

### Notes
If a middleware doesn't call `call_next()` it raises `middlewares.CallNextNotUsedError`. It means that the middleware forcibly decline middlewares handlers and response should be sent immediately without routers running. `call_routers` should looks like this:
```python
import middletools


async def call_routers(self, request):
    try:
        read_afterwords = await middletools.read_forewords(
            *self.middlewares, inbox_value=request
        )
        for router in self.routers:
            ... # Pass request to routers and check it matched
            response = ...
            await read_afterwords(response)
            return response
    except middletools.CallNextNotUsedError:
        return SomeBadResponseBecauseNotRouted(400, "Require a header!")
    
```
***
If a middleware doesn't return anything, middlewares dispatching declined forcibly too but after routers handled. (Return nothing means there isn't any `return` or `return None` used). It raises `middlewares.NothingReturnedError`
```python
import middletools


async def call_routers(self, request):
    try:
        read_afterwords = await middletools.read_forewords(
            *self.middlewares, inbox_value=request
        )
        for router in self.routers:
            ... # Pass request to routers and check it matched
            response = ...
            await read_afterwords(response)
            return response
    except middletools.CallNextNotUsedError:
        return SomeBadResponseBecauseNotRouted(400, "Require a header!")
    except middletools.NothingReturnedError:
        return SomeBadResponseBecauseMiddlewareDntReturnResponse(
            500, "Oops, internal server error"
        )
```
