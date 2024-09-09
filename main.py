from fastapi import FastAPI, Path

import time

from rate_limiter import rate_limiter
from stores.config_store import Config, config_store

app = FastAPI(openapi_url="/api/v1/openapi.json")


@app.post("/api/configure")
def configure_rate_limiter(config: Config):
    """
    Endpoint to configure the rate limiter with interval and limit settings.
    :param config: The configuration for the rate limiter.
    :return: The saved configuration in json format.
    """
    config_store.set_config(config)
    return config


@app.get("/api/is_rate_limited/{unique_token}")
async def is_rate_limited(
        unique_token: str = Path(...,
                                 title="Unique Token",
                                 description="Unique token for the user",
                                 max_length=100),
):
    """
    Endpoint to check if a user is rate-limited based on their unique token.
    :param background_tasks: Task handler for background updates.
    :param unique_token: The unique identifier for the user.
    :return: Boolean indicating if the user is rate-limited. Returns "true" or "false" in the api response
    """
    now = time.time()
    return await rate_limiter.is_rate_limited(unique_token, now)
