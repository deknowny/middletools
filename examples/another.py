import middlewares


# This is an example of a middlewares
# That just checks that a header exists in
# in request and add a header to the server's response
@middlewares.make(proto="https")  # Example parametrize
async def custom_middleware(request, call_next):
    if "X-Required-Request-Header" in request.headers:
        response = await call_next()
        response.headers["X-Required-Response-Header"] = "some value"


# An example of an API router
async def router(request) -> dict:
    return {
        "some_api_response": "ok"
    }


# Function that handler request and run routers handling
async def route_some_request(request, run_routers):
    collection_of_middlewares = [custom_middleware()]

    # Run every middleware until they call `call_next` first
    try:
        read_afterword = await middlewares.read_forewords(
            *collection_of_middlewares
        )

    # Call next hasn't been run
    except middlewares.CallNextNotUsedError:
        return 400, "Bad request"
    else:
        router_response = run_routers(request)
        response = await read_afterword(router_response)
        return 200, response


