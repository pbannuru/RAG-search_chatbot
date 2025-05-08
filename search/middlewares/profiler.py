import os
import time
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pyinstrument import Profiler

from app.middlewares.exception import ExceptionHandlerMiddleware
from pyinstrument.renderers.html import HTMLRenderer
from pyinstrument.renderers.speedscope import SpeedscopeRenderer
from app.config.env import environment


def register_profiler_middlewares(app: FastAPI):

    if environment.PROFILING_ENABLED is True:

        @app.middleware("http")
        async def profile_request(request: Request, call_next: Callable):
            """Profile the current request

            Taken from https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
            with small improvements.

            """
            # we map a profile type to a file extension, as well as a pyinstrument profile renderer
            profile_type_to_ext = {"html": "html", "speedscope": "speedscope.json"}
            profile_type_to_renderer = {
                "html": HTMLRenderer,
                "speedscope": SpeedscopeRenderer,
            }
            profiler_type_to_fastapi_response_formatter = {
                "html": HTMLResponse,
                "speedscope": JSONResponse,
            }

            # if the `profile=true` HTTP query argument is passed, we profile the request
            if request.query_params.get("profile", "false").lower() == "true":

                # The default profile format is html. Options: ['html', 'speedscope']
                profile_type = request.query_params.get("profile_format", "html")

                # The default profile time measurement is system. Options: ['system', 'frombeginning', 'process_time']
                profile_time_measurement = request.query_params.get(
                    "profile_time_measurement", "system"
                )

                # The default profile returns api results. Options: ['api', 'profiler']
                profile_returns = request.query_params.get("profile_returns", "api")

                # we profile the request along with all additional middlewares, by interrupting
                # the program every 1ms1 and records the entire stack at that point
                with Profiler(interval=0.001, async_mode="enabled") as profiler:
                    response = await call_next(request)

                # we dump the profiling into a file
                extension = profile_type_to_ext[profile_type]
                renderer = profile_type_to_renderer[profile_type]()
                fastapi_response_formatter = (
                    profiler_type_to_fastapi_response_formatter[profile_type]
                )

                if profile_time_measurement == "system":
                    t = time.time()
                elif profile_time_measurement == "frombeginning":
                    t = time.time() - environment.PROGRAM_START_TIME
                elif profile_time_measurement == "process_time":
                    t = time.process_time()

                filename = f"profiler{request.url.path}/profile-{t}.{extension}"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(
                    filename,
                    "w",
                ) as out:
                    out.write(profiler.output(renderer=renderer))

                if profile_returns == "api":
                    return response
                elif profile_returns == "profiler":
                    return HTMLResponse(
                        profiler.output(renderer=renderer),
                    )

            # Proceed without profiling
            return await call_next(request)
